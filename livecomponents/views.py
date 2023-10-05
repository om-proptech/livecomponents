from django.http import HttpRequest, HttpResponse
from django.template import Context, Template

from livecomponents.manager import get_state_manager
from livecomponents.types import CallMethodRequestArgs


def call_method(request: HttpRequest):
    args = CallMethodRequestArgs(**request.GET.dict())
    state_manager = get_state_manager()
    state_manager.call_component_method(
        request, args.component_name, args.get_state_address(), args.method_name
    )
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
