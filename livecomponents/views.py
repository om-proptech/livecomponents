from django.http import HttpRequest, HttpResponse
from django.template import Context, Template
from django_components.component_registry import registry
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager import get_state_manager


class CallMethodRequestArgs(BaseModel):
    component_name: str
    session_id: str
    component_id: str
    method_name: str


def call_method(request: HttpRequest):
    args = CallMethodRequestArgs(**request.GET.dict())
    state_store = get_state_manager()
    component_cls = get_component_class(args.component_name)
    state = state_store.get_or_create_component_state(
        args.session_id, args.component_id, component_cls.init_state
    )

    method = getattr(component_cls, args.method_name)
    method(state)

    state_store.set_component_state(args.session_id, args.component_id, state)
    return re_render_component(request, args)


def re_render_component(
    request: HttpRequest, args: CallMethodRequestArgs
) -> HttpResponse:
    template = (
        f'{{% load component_tags %}}{{% component "{args.component_name}" '
        f'session_id="{args.session_id}" component_id="{args.component_id}" %}}'
    )
    rendered = Template(template).render(
        Context({"live_component_session_id": args.session_id})
    )
    return HttpResponse(rendered)


def get_component_class(component_name: str) -> type[LiveComponent]:
    return registry.get(component_name)
