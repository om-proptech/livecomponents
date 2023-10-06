from urllib.parse import urlencode

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

from livecomponents.sessions import get_session_id

register = template.Library()


@register.simple_tag(takes_context=True)
def call_method(
    context, component_name: str, component_id: str, method_name: str
) -> str:
    session_id = context["LIVECOMPONENTS_SESSION_ID"]
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
def livecomponents_session_id(context) -> str:
    """Return the session ID for the live components session."""
    request = context["request"]
    return get_session_id(request)


@register.filter(name="css_escape")
def css_escape(value: str) -> str:
    return mark_safe("".join(char if char.isalnum() else f"\\{char}" for char in value))
