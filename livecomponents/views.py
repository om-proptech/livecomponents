from django.http import HttpRequest, HttpResponse
from django.template import Context, Template
from django_components.component_registry import registry
from pydantic import BaseModel

from livecomponents import LiveComponent


class CallMethodRequestArgs(BaseModel):
    component_name: str
    session_id: str
    component_id: str
    method_name: str


def call_method(request: HttpRequest):
    args = CallMethodRequestArgs(**request.GET.dict())

    component_cls = get_component_class(args.component_name)
    state = component_cls.get_or_create_state(args.session_id, args.component_id)

    method = getattr(state, args.method_name)
    method()

    component_cls.save_state(args.session_id, args.component_id, state)

    return re_render_component(args)


def re_render_component(args: CallMethodRequestArgs) -> HttpResponse:
    template = (
        f'{{% load component_tags %}}{{% component "{args.component_name}" '
        f'session_id="{args.session_id}" component_id="{args.component_id}" %}}'
    )
    rendered = Template(template).render(Context())
    rendered_with_oob = add_swap_oob_attribute(rendered)
    return HttpResponse(rendered_with_oob)


def add_swap_oob_attribute(content: str) -> str:
    """Prepend the first found ID with hx-swap-oob="true"."""
    # See: https://htmx.org/docs/#oob_swaps
    return content.replace("id=", 'hx-swap-oob="true" id=', 1)


def get_component_class(component_name: str) -> type[LiveComponent]:
    return registry.get(component_name)
