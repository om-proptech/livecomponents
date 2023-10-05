from django.http import HttpRequest, HttpResponse
from django.template import Context, Template

from livecomponents.manager import get_state_manager
from livecomponents.manager.manager import CallContext
from livecomponents.types import CallMethodRequestArgs, ComponentAddress


def call_method(request: HttpRequest):
    args = CallMethodRequestArgs(**request.GET.dict())
    state_manager = get_state_manager()
    call_context = state_manager.call_component_method(
        request, args.component_name, args.get_state_address(), args.method_name
    )
    rendered_components = [
        re_render_component(call_context, component_address)
        for component_address in call_context.dirty_components
    ]
    return HttpResponse("\n".join(rendered_components))


def re_render_component(
    call_context: CallContext, component_address: ComponentAddress
) -> str:
    template = (
        f"{{% load component_tags %}}"
        f'{{% component "{component_address.name}" '
        f'session_id="{component_address.state_address.session_id}" '
        f'component_id="{component_address.state_address.component_id}" %}}'
    )
    rendered = Template(template).render(
        Context(
            {"live_component_session_id": component_address.state_address.session_id}
        )
    )
    return rendered
