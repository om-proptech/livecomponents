from urllib.parse import urlencode

from django import template
from django.template.base import FilterExpression
from django.urls import reverse
from django_components.templatetags.component_tags import (
    ComponentNode,
    check_for_isolated_context_keyword,
    parse_component_with_args,
)

from livecomponents.sessions import get_session_id

register = template.Library()


@register.simple_tag(takes_context=True)
def call_method(
    context, component_name: str, component_id: str, method_name: str
) -> str:
    session_id = context["live_component_session_id"]
    url = reverse(
        "livecomponents:call-method",
    )
    kwargs = urlencode(
        {
            "component_name": component_name,
            "session_id": session_id,
            "component_id": component_id,
            "method_name": method_name,
        }
    )
    return f"{url}?{kwargs}"


@register.simple_tag(takes_context=True)
def live_component_session_id(context) -> str:
    """Return the session ID for the live components session."""
    request = context["request"]
    return get_session_id(request)


@register.tag(name="livecomponent")
def do_live_component(parser, token):
    bits = token.split_contents()
    bits, isolated_context = check_for_isolated_context_keyword(bits)
    component_name, context_args, context_kwargs = parse_component_with_args(
        parser, bits, "component"
    )
    # context_kwargs["session_id"] =
    return ComponentNode(
        FilterExpression(component_name, parser),
        context_args,
        context_kwargs,
        isolated_context=isolated_context,
    )
