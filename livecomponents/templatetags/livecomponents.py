import secrets
from typing import Any, cast
from urllib.parse import urlencode

from django import template
from django.forms.utils import flatatt
from django.template import Context, TemplateSyntaxError
from django.template.base import Parser, Token, TokenType
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_components import ComponentNode, registry
from django_components.slots import _is_extracting_fill
from django_components.util.template_tag import bits_from_tag
from djc_core.template_parser import parse_tag

from livecomponents.const import DEFAULT_OWN_ID, HIER_SEP, TYPE_SEP
from livecomponents.sentry_utils import start_span
from livecomponents.sessions import get_session_id
from livecomponents.types import StateAddress
from livecomponents.utils import find_component_id, find_session_id, get_ancestor_id

register = template.Library()


@register.simple_tag
def component_id(*args) -> str:
    """Component ID, built from type and ID pairs, following one after another.

    For example:

    {% component_id "table" "primary" "row" 1 "cell" "x" as cell_x %}

    will return

    |table:primary|row:1|cell:x
    """
    chunks = [""]
    for type_, id_ in zip(args[::2], args[1::2]):
        chunks.append(f"{type_}{TYPE_SEP}{id_}")
    return HIER_SEP.join(chunks)


@register.simple_tag
def component_ancestor(component_id_: str, ancestor_type: str) -> str:
    """Return the ID of the closest ancestor component of the given type.

    For example:

    {% component_ancestor component_id "table" %}

    Will return the full ID of the table component, that is the ancestor of the given
    component (e.g., "|table:primary").
    """
    return get_ancestor_id(component_id_, ancestor_type) or ""


@register.simple_tag(takes_context=True)
def call_command(context, component_id: str, command_name: str) -> str:
    """Return the URL for calling a command on a component."""
    session_id = find_session_id(context)
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
        "key": component_id,
    }
    return flatatt(attrs)


@register.simple_tag
def component_selector(component_id: str) -> str:
    """Return the CSS selector for the component with the given ID.

    Can be used to select the component in JavaScript code. For example:

    ```javascript
    const element = document.querySelector({% component_selector component_id %});
    ```

    Note that the returned value is already quoted, so you don't need to add quotes
    around it.
    """
    return mark_safe(f"\"[data-livecomponent-id='{css_escape(component_id)}']\"")


@register.simple_tag
def livecomponents_session_id() -> str:
    """Return the session ID for the live components session."""
    return get_session_id()


@register.filter(name="css_escape")
def css_escape(value: str) -> str:
    return mark_safe("".join(char if char.isalnum() else f"\\{char}" for char in value))


@register.simple_tag
def no_morph():
    """Return a key that disables morphing for the component.

    Random key is generated to prevent morphing of the component.
    See https://alpinejs.dev/plugins/morph#keys for more details.

    Usage example:

        <textarea {% no_morph %}></textarea>

    This way, the textarea DOM element will always be replaced, not morphed, which,
    for example, results in updating the component state from the server side.
    """
    return mark_safe(f'key="{secrets.token_urlsafe(8)}"')


# Resolve the unwrapped ComponentNode.render() once, at import time. The
# wrapped ComponentNode.render() (what you get by calling super().render())
# re-resolves the tag inputs from the context, which would discard the changes
# that BaseLiveComponentNode.render() makes to them. Resolving `__wrapped__`
# here makes an incompatible django-components upgrade fail fast at startup
# instead of mid-render.
_COMPONENT_NODE_RENDER = ComponentNode.render.__wrapped__  # type: ignore[attr-defined]


class BaseLiveComponentNode(ComponentNode):
    """Base class for the `{% livecomponent %}` and `{% livecomponent_block %}` tags.

    A subclass of django-components' ComponentNode that additionally:

    - Saves the raw template source of the tag to the state store, so the
      component can be re-rendered standalone (outside of the original page)
      when one of its commands is called.
    - Supports the `save_context` kwarg to save (and later restore) selected
      context variables along with the component.
    - Picks up the "full_component_id" context variable that the re-render
      view sets to address the component in the state store.
    """

    # The raw template source of the whole tag (including the body and the end
    # tag for the block form). Reconstructed from the consumed parser tokens
    # and assigned by _parse_livecomponent_tag() right after parsing.
    template_source: str | None = None

    @classmethod
    def parse(
        cls, parser: Parser, token: Token, **kwargs: Any
    ) -> "BaseLiveComponentNode":
        # Skip ComponentNode.parse(): it dynamically subclasses the node class
        # to set the tag names, and does not pass extra kwargs through. Our
        # node classes define `tag`/`end_tag` statically, so we can call
        # BaseNode.parse() directly.
        node = super(ComponentNode, cls).parse(parser, token, **kwargs)
        return cast("BaseLiveComponentNode", node)

    def render(self, context: Context, *args: Any, **kwargs: Any) -> str:
        # Do not render (or touch the state store) while django-components is
        # only extracting fills from the surrounding component tag.
        if _is_extracting_fill(context):
            return ""

        # "save_context" is consumed by the tag; it is not passed to the
        # component. Whether the save/restore machinery runs is decided by the
        # *presence* of the kwarg, not by its resolved value: on command
        # re-renders, a save_context passed as a template variable resolves to
        # "" (the variable only exists in the original page context), but the
        # previously saved context still has to be restored.
        has_save_context = "save_context" in kwargs
        save_context = kwargs.pop("save_context", "")
        save_context_vars = [
            value.strip() for value in save_context.split(",") if value.strip()
        ]

        # Move "full_component_id" from context to component kwargs. The
        # re-render view sets it to address the top-level re-rendered
        # component; it must not leak to nested components.
        full_component_id = None
        if context.get("full_component_id"):
            full_component_id = context["full_component_id"]
            kwargs["full_component_id"] = full_component_id
            context["full_component_id"] = None

        state_addr = self.get_state_addr(context, kwargs)
        sentry_arg = f"[{state_addr.component_id}]"

        # template_source is always set by _parse_livecomponent_tag() right
        # after parsing.
        assert self.template_source is not None
        with start_span(f"save_component_template({sentry_arg})"):
            self.save_component_template(state_addr, self.template_source)

        if has_save_context:
            with start_span(f"save_or_restore_context({sentry_arg})"):
                restored_context = self.save_or_restore_context(
                    state_addr, context, save_context_vars
                )
            if restored_context is not context:
                # The context was restored from the state store (this is a
                # command re-render). The tag kwargs have been resolved
                # against the pre-restore context, where the page variables
                # don't exist, so re-resolve them against the restored one.
                context = restored_context
                args, kwargs = self.resolve_tag_params(context, full_component_id)

        return _COMPONENT_NODE_RENDER(self, context, *args, **kwargs)

    def resolve_tag_params(
        self, context: Context, full_component_id: str | None
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """Resolve the tag args and kwargs against the given context.

        The params resolver has been compiled by the BaseNode render wrapper
        before our render() implementation runs, so it is always available.
        """
        resolved_args, resolved_kwargs = self._params_resolver(context)
        kwargs = dict(resolved_kwargs)
        kwargs.pop("save_context", None)
        if full_component_id:
            kwargs["full_component_id"] = full_component_id
        return tuple(resolved_args), kwargs

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
        save_context_vars: list[str],
    ):
        from livecomponents.manager import get_state_manager

        state_manager = get_state_manager()

        sentry_arg = f"[{state_addr.component_id}]"
        if state_manager.component_initialized(state_addr):
            # Use the same fallbacks as get_state_addr(): under the "only"
            # isolation flag, the page-level "request" and
            # "LIVECOMPONENTS_SESSION_ID" keys don't survive the isolated
            # context copy.
            effective_context = {
                "LIVECOMPONENTS_SESSION_ID": find_session_id(context),
            }
            request = context.get("request")
            if request is not None:
                effective_context["request"] = request
            with start_span(f"get_component_context({sentry_arg})"):
                restored_context = state_manager.get_component_context(state_addr)
            new_context = context.new(effective_context)
            new_context.update(restored_context)
            return new_context
        else:
            effective_context = {
                var: context[var] for var in save_context_vars if var in context
            }
            with start_span(f"set_component_context({sentry_arg})"):
                state_manager.set_component_context(state_addr, effective_context)
            return context

    def get_state_addr(
        self, context: Context, resolved_kwargs: dict[str, Any]
    ) -> StateAddress:
        session_id = find_session_id(context)
        component_id = find_component_id(
            full_component_id=resolved_kwargs.get("full_component_id"),
            component_name=self.name,
            own_id=resolved_kwargs.get("own_id", DEFAULT_OWN_ID),
            parent_id=resolved_kwargs.get("parent_id", ""),
        )
        return StateAddress(session_id=session_id, component_id=component_id)


# NOTE: allowed_flags must be re-declared on each node class (even though the
# value is inherited from ComponentNode) so that django-components' NodeMeta
# registers the flags for OUR tag names with the template parser. Without it,
# the "only" flag would be parsed as a positional argument.
class LiveComponentNode(BaseLiveComponentNode):
    """The `{% livecomponent %}` tag: the inline form without slot fills."""

    tag = "livecomponent"
    end_tag = None
    allowed_flags = ComponentNode.allowed_flags


class LiveComponentBlockNode(BaseLiveComponentNode):
    """The `{% livecomponent_block %}` tag: the block form that accepts fills."""

    tag = "livecomponent_block"
    end_tag = "endlivecomponent_block"
    allowed_flags = ComponentNode.allowed_flags


def _render_token(token: Token) -> str:
    """Reconstruct the raw template source of a single parser token."""
    if token.token_type == TokenType.TEXT:
        return token.contents
    elif token.token_type == TokenType.VAR:
        return "{{ " + token.contents + " }}"
    elif token.token_type == TokenType.BLOCK:
        return "{% " + token.contents + " %}"
    elif token.token_type == TokenType.COMMENT:
        return "{# " + token.contents + " #}"
    raise ValueError(f"Unknown token type: {token.token_type}")


def _parse_livecomponent_tag(
    parser: Parser, token: Token, node_cls: type[BaseLiveComponentNode]
) -> BaseLiveComponentNode:
    """Extract the component name from the tag and parse the rest of the tag.

    Mirrors what django-components' ComponentRegistry does for the
    `{% component %}` tag: the component name (the first positional argument)
    is removed from the token, and the remaining arguments are passed to the
    component.

    Additionally, reconstructs the raw template source of the whole tag
    (including the body of the block form) from the tokens consumed by the
    parser, and stores it on the node as `template_source`. The source is
    rebuilt from the consumed tokens — rather than from django-components'
    `BaseNode.contents` — because `contents` stops at the first matching end
    tag and would truncate the source of a `{% livecomponent_block %}` nested
    inside another one.

    NOTE: the tag is parsed twice (parse_tag() here and again inside
    BaseNode.parse()). This is deliberate: parse_tag() is the only tokenizer
    that correctly extracts the component name when the tag uses
    django-components syntax extensions, such as template tags inside
    attribute values (`key="{% lorem 3 w %}"`).
    """
    original_start_tag = "{% " + token.contents + " %}"
    tag = parse_tag(original_start_tag)
    bits = bits_from_tag(tag)
    if len(bits) < 2:
        raise TemplateSyntaxError(
            f"'{node_cls.tag}' tag requires a component name "
            f"as the first positional argument"
        )
    name_bit = bits[1]
    if not (
        len(name_bit) >= 2 and name_bit[0] in "\"'" and name_bit[-1] == name_bit[0]
    ):
        raise TemplateSyntaxError(
            f"Component name in the '{node_cls.tag}' tag must be "
            f"a quoted string literal, got: {name_bit}"
        )
    component_name = name_bit[1:-1]

    # Snapshot the parser tokens so we can reconstruct the raw source of the
    # tag body (everything up to and including the matching end tag) from the
    # tokens that BaseNode.parse() consumes. Django's parser treats
    # `parser.tokens` as a stack (the next token is the LAST list item), so
    # the consumed tokens are the tail of the snapshot, in reverse order.
    tokens_before = parser.tokens[:]

    # Put back the tag bits without the component name, and restore the
    # original token contents after parsing: when this tag is nested inside
    # another livecomponent tag, the outer tag reconstructs its body source
    # from the same token objects, and must see this tag's component name.
    original_token_contents = token.contents
    token.contents = " ".join([bits[0], *bits[2:]])
    try:
        node = node_cls.parse(parser, token, registry=registry, name=component_name)
    finally:
        token.contents = original_token_contents

    consumed_tokens = tokens_before[len(parser.tokens) :]
    body_source = "".join(
        _render_token(consumed) for consumed in reversed(consumed_tokens)
    )
    node.template_source = original_start_tag + body_source
    return node


@register.tag(name="livecomponent")
def do_livecomponent(parser: Parser, token: Token) -> BaseLiveComponentNode:
    return _parse_livecomponent_tag(parser, token, LiveComponentNode)


@register.tag(name="livecomponent_block")
def do_livecomponent_block(parser: Parser, token: Token) -> BaseLiveComponentNode:
    return _parse_livecomponent_tag(parser, token, LiveComponentBlockNode)
