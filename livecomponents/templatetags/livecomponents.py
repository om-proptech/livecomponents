from urllib.parse import urlencode

from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def call_method(id: str, method_name: str) -> str:
    url = reverse(
        "livecomponents:call-method",
    )
    kwargs = urlencode({"id": id, "method_name": method_name})
    return f"{url}?{kwargs}"
