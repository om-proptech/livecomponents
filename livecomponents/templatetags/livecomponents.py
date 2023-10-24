from collections.abc import Iterable
from urllib.parse import urlencode

from django import template
from django.forms.utils import flatatt
from django.template import Context, NodeList, TemplateSyntaxError
from django.template.base import FilterExpression, token_kwargs
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_components.templatetags.component_tags import (
    ComponentNode,
    ImplicitFillNode,
    NamedFillNode,
    block_has_content,
    check_for_isolated_context_keyword,
    parse_component_with_args,
    safe_resolve,
    try_parse_as_default_fill,
    try_parse_as_named_fill_tag_set,
)

from livecomponents.sessions import get_session_id
from livecomponents.templatetags.utils import (
    capture_used_tokens,
    get_save_context_vars,
    render_save_context_vars,
)
from livecomponents.types import StateAddress
from livecomponents.utils import find_component_id

register = template.Library()


@register.tag(name="only_with")
def do_only_with(parser, token):
    bits = token.split_contents()
    remaining_bits = bits[1:]
    new_context = token_kwargs(remaining_bits, parser)
    if not new_context:
        raise TemplateSyntaxError(
            "%r expected at least one variable assignment" % bits[0]
        )
    if remaining_bits:
        raise TemplateSyntaxError(
            f"{bits[0]!r} received an invalid token: {remaining_bits[0]!r}"
        )

    nodelist = parser.parse(("endonly_with",))
    parser.delete_first_token()
    return OnlyWithNode(nodelist, new_context)


class OnlyWithNode(template.Node):
    def __init__(self, nodelist, new_context):
        self.nodelist = nodelist
        self.new_context = new_context

    def render(self, context):
        resolved_context = {
            key: safe_resolve(value, context) for key, value in self.new_context.items()
        }
        effective_context = {
            **resolved_context,
            "request": context["request"],
            "LIVECOMPONENTS_SESSION_ID": context["LIVECOMPONENTS_SESSION_ID"],
        }
        isolated_context = context.new()
        with isolated_context.push(effective_context):
            return self.nodelist.render(isolated_context)


@register.simple_tag(takes_context=True)
def call_command(context, component_id: str, command_name: str) -> str:
    session_id = context["LIVECOMPONENTS_SESSION_ID"]
    url = reverse(
        "livecomponents:call-command",
    )
    kwargs = urlencode(
        {
            "session_id": session_id,
            "component_id": component_id,
            "command_name": command_name,
        }
    )
    return f"{url}?{kwargs}"


@register.simple_tag
def component_attrs(component_id: str, swap_style="morph") -> str:
    """Convert component ID to component attrs.

    They are supposed to be added as attributes to the root HTML
    element of the component.

    The `swap_style` parameter is used to determine how the component has to update
    its state. See https://htmx.org/attributes/hx-swap-oob/ for more details.
    """
    attrs = {
        "data-livecomponent-id": component_id,
        "hx-swap-oob": (
            f"{swap_style}:[data-livecomponent-id='{css_escape(component_id)}']"
        ),
    }
    return flatatt(attrs)


@register.simple_tag
def livecomponents_session_id() -> str:
    """Return the session ID for the live components session."""
    return get_session_id()


@register.filter(name="css_escape")
def css_escape(value: str) -> str:
    return mark_safe("".join(char if char.isalnum() else f"\\{char}" for char in value))


@register.tag(name="livecomponent")
def do_livecomponent(parser, token):
    with capture_used_tokens(parser, token) as captured_tokens:
        bits = token.split_contents()
        bits, isolated_context = check_for_isolated_context_keyword(bits)
        component_name, context_args, context_kwargs = parse_component_with_args(
            parser, bits, "livecomponent"
        )
        save_context_vars = get_save_context_vars(context_kwargs)
    return LiveComponentNode(
        FilterExpression(component_name, parser),
        context_args,
        context_kwargs,
        isolated_context=isolated_context,
        save_context_vars=save_context_vars,
        component_template=captured_tokens.render(),
    )


@register.tag(name="livecomponent_block")
def do_livecomponent_block(parser, token):
    # A copy-paste of django_components.templatetags.component_tags.do_component_block
    # with the name changed from "component_block" to "livecomponent_block",
    # and ComponentNode to LiveComponentNode.

    with capture_used_tokens(parser, token) as captured_tokens:
        # See the original function for more details.
        bits = token.split_contents()
        bits, isolated_context = check_for_isolated_context_keyword(bits)
        component_name, context_args, context_kwargs = parse_component_with_args(
            parser, bits, "livecomponent_block"
        )
        save_context_vars = get_save_context_vars(context_kwargs)
        body: NodeList = parser.parse(parse_until=["endlivecomponent_block"])
        parser.delete_first_token()

    fill_nodes = ()
    if block_has_content(body):
        for parse_fn in (
            try_parse_as_default_fill,
            try_parse_as_named_fill_tag_set,
        ):
            fill_nodes = parse_fn(body)
            if fill_nodes:
                break
        else:
            raise TemplateSyntaxError(
                "Illegal content passed to 'livecomponent_block' tag pair. "
                "Possible causes: 1) Explicit 'fill' tags cannot occur alongside other "
                "tags except comment tags; 2) Default (default slot-targeting) content "
                "is mixed with explict 'fill' tags."
            )

    component_node = LiveComponentNode(
        FilterExpression(component_name, parser),
        context_args,
        context_kwargs,
        isolated_context=isolated_context,
        save_context_vars=save_context_vars,
        fill_nodes=fill_nodes,
        component_template=captured_tokens.render(),
    )
    return component_node


class LiveComponentNode(ComponentNode):
    def __init__(
        self,
        name_fexp: FilterExpression,
        context_args,
        context_kwargs,
        isolated_context=False,
        save_context_vars: FilterExpression | None = None,
        fill_nodes: ImplicitFillNode | Iterable[NamedFillNode] = (),
        component_template: str | None = None,
    ):
        super().__init__(
            name_fexp,
            context_args,
            context_kwargs,
            isolated_context=isolated_context,
            fill_nodes=fill_nodes,
        )
        self.component_template = component_template
        self.save_context_vars = save_context_vars

    def render(self, context: Context):
        # move "full_component_id" from context to context_kwargs
        if "full_component_id" in context:
            self.context_kwargs["full_component_id"] = context["full_component_id"]
            context["full_component_id"] = None

        state_addr = self.get_state_addr(context)
        if self.component_template is not None:
            self.save_component_template(state_addr, self.component_template)

        rendered_save_context_vars = render_save_context_vars(
            self.save_context_vars, context
        )
        if rendered_save_context_vars:
            context = self.save_or_restore_context(
                state_addr, context, rendered_save_context_vars
            )
        return super().render(context)

    def save_component_template(
        self, state_addr: StateAddress, component_template: str
    ):
        from livecomponents.manager import get_state_manager

        state_manager = get_state_manager()
        state_manager.save_component_template(state_addr, component_template)

    def save_or_restore_context(
        self,
        state_addr: StateAddress,
        context: Context,
        rendered_save_context_vars: list[str],
    ):
        from livecomponents.manager import get_state_manager

        state_manager = get_state_manager()
        if state_manager.is_component_initialized(state_addr):
            effective_context = {
                "request": context["request"],
                "LIVECOMPONENTS_SESSION_ID": context["LIVECOMPONENTS_SESSION_ID"],
            }
            restored_context = state_manager.get_component_context(state_addr)
            new_context = context.new(effective_context)
            new_context.update(restored_context)
            return new_context
        else:
            effective_context = {
                var: context[var]
                for var in rendered_save_context_vars
                if var in context
            }
            state_manager.set_component_context(state_addr, effective_context)
            return context

    def get_state_addr(self, context: Context):
        from livecomponents.component import DEFAULT_OWN_ID

        # Context kwargs are the keyword arguments, passed to the component itself.
        # They can contain variables, that will be resolved against the parent context.
        resolved_component_name = self.name_fexp.resolve(context)
        resolved_context_kwargs = {
            key: safe_resolve(kwarg, context)
            for key, kwarg in self.context_kwargs.items()
        }
        session_id = context["LIVECOMPONENTS_SESSION_ID"]
        component_id = find_component_id(
            full_component_id=resolved_context_kwargs.get("full_component_id"),
            component_name=resolved_component_name,
            own_id=resolved_context_kwargs.get("own_id", DEFAULT_OWN_ID),
            parent_id=resolved_context_kwargs.get("parent_id", ""),
        )
        return StateAddress(session_id=session_id, component_id=component_id)
