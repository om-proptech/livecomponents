import json
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.template import RequestContext, Template

from livecomponents.manager import get_state_manager
from livecomponents.manager.manager import CallContext
from livecomponents.types import CallMethodRequestArgs, StateAddress


def call_method(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse("Only POST allowed", status=405)
    args = CallMethodRequestArgs(**request.GET.dict())
    state_manager = get_state_manager()
    kwargs = parse_json_body(request)
    call_context = state_manager.call_component_method(
        request,
        args.get_state_address(),
        args.method_name,
        kwargs=kwargs,
    )

    dirty_components = deduplicate_dirty_components(call_context.dirty_components)

    rendered_components = [
        re_render_component(call_context, component_address)
        for component_address in dirty_components
    ]
    return HttpResponse("\n".join(rendered_components))


def parse_json_body(request: HttpRequest) -> dict[str, Any]:
    if request.body == b"":
        return {}
    return json.loads(request.body.decode())


def deduplicate_dirty_components(dirty_components: set[StateAddress]):
    """De-duplicate dirty components.

    Do not schedule child comoponents re-render if parent component re-render
    is already scheduled. Define the parent-child relationship by comparing
    component ids: parent component ID is a prefix of child component ID.
    """
    sorted_dirty_components = sorted(dirty_components, key=lambda x: x.component_id)
    deduplicated: set[StateAddress] = set()
    for component_address in sorted_dirty_components:
        if not any(
            component_address.component_id.startswith(x.component_id)
            for x in deduplicated
        ):
            deduplicated.add(component_address)
    return deduplicated


def re_render_component(call_context: CallContext, state_address: StateAddress) -> str:
    template = (
        f"{{% load component_tags %}}"
        f'{{% component "{state_address.get_component_name()}" '
        f'full_component_id="{state_address.component_id}" %}}'
    )
    rendered = Template(template).render(
        RequestContext(
            call_context.request,
            {"LIVECOMPONENTS_SESSION_ID": state_address.session_id},
        )
    )
    return rendered
