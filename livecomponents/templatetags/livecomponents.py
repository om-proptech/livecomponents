from urllib.parse import urlencode

from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def call_method(
    component_name: str, session_id: str, component_id: str, method_name: str
) -> str:
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
