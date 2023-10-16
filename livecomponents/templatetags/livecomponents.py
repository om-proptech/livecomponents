from collections.abc import Iterable
from urllib.parse import urlencode

from django import template
from django.forms.utils import flatatt
from django.template import Context, NodeList, TemplateSyntaxError
from django.template.base import FilterExpression, Parser, Token
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
from livecomponents.types import StateAddress
from livecomponents.utils import find_component_id

register = template.Library()


@register.simple_tag(takes_context=True)
def call_method(context, component_id: str, method_name: str) -> str:
    session_id = context["LIVECOMPONENTS_SESSION_ID"]
    url = reverse(
        "livecomponents:call-method",
    )
    kwargs = urlencode(
        {
            "session_id": session_id,
            "component_id": component_id,
            "method_name": method_name,
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


@register.simple_tag(takes_context=True)
def livecomponents_session_id(context) -> str:
    """Return the session ID for the live components session."""
    request = context["request"]
    return get_session_id(request)


@register.filter(name="css_escape")
def css_escape(value: str) -> str:
    return mark_safe("".join(char if char.isalnum() else f"\\{char}" for char in value))


@register.tag(name="livecomponent")
def do_livecomponent(parser, token):
    bits = token.split_contents()
    bits, isolated_context = check_for_isolated_context_keyword(bits)
    component_name, context_args, context_kwargs = parse_component_with_args(
        parser, bits, "livecomponent"
    )
    return LiveComponentNode(
        FilterExpression(component_name, parser),
        context_args,
        context_kwargs,
        isolated_context=isolated_context,
        component_template=_get_component_template(parser, token),
    )


@register.tag(name="livecomponent_block")
def do_livecomponent_block(parser, token):
    # A copy-paste of django_components.templatetags.component_tags.do_component_block
    # with the name changed from "component_block" to "livecomponent_block",
    # and ComponentNode to LiveComponentNode.

    # See the original function for more details.
    bits = token.split_contents()
    bits, isolated_context = check_for_isolated_context_keyword(bits)
    component_name, context_args, context_kwargs = parse_component_with_args(
        parser, bits, "livecomponent_block"
    )
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
        fill_nodes=fill_nodes,
        component_template=_get_component_template(parser, token),
    )
    return component_node


class LiveComponentNode(ComponentNode):
    def __init__(
        self,
        name_fexp: FilterExpression,
        context_args,
        context_kwargs,
        isolated_context=False,
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

    def render(self, context: Context):
        # move "full_component_id" from context to context_kwargs
        if "full_component_id" in context:
            self.context_kwargs["full_component_id"] = context["full_component_id"]
            context["full_component_id"] = None

        if self.component_template is not None:
            self.save_component_template(context)
        return super().render(context)

    def save_component_template(self, context: Context):
        from livecomponents.component import DEFAULT_OWN_ID
        from livecomponents.manager import get_state_manager

        if not self.component_template:
            raise ValueError("Component template is not set")

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
        state_addr = StateAddress(session_id=session_id, component_id=component_id)

        state_manager = get_state_manager()
        state_manager.save_component_template(state_addr, self.component_template)


def _get_component_template(parser: Parser, token: Token) -> str | None:
    if not parser.origin or not parser.origin.loader:
        # When we re-render the component, we don't have the original template
        return None
    contents = parser.origin.loader.get_contents(parser.origin)
    return contents[token.position[0] : parser.tokens[-1].position[0]]
