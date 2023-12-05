import json
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.template import RequestContext, Template

from livecomponents.logging import logger
from livecomponents.manager import get_state_manager
from livecomponents.manager.manager import CallContext
from livecomponents.types import CallMethodRequestArgs, StateAddress


def call_command(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse("Only POST allowed", status=405)
    args = CallMethodRequestArgs(**request.GET.dict())
    state_manager = get_state_manager()
    kwargs = parse_body(request)

    if not state_manager.session_exists(args.session_id):
        logger.warning(
            "Session %s does not exist. It may have expired", args.session_id
        )
        return HttpResponse("Session does not exist. It may have expired", status=410)

    call_context = state_manager.call_component_method(
        request,
        args.get_state_address(),
        args.command_name,
        kwargs=kwargs,
    )

    headers = call_context.execution_results.response_headers

    if not call_context.execution_results.is_partial_render_necessary():
        # Shortcut for full page refresh
        return HttpResponse(
            headers=call_context.execution_results.response_headers,
        )

    dirty_components = deduplicate_dirty_components(
        call_context.execution_results.dirty_components
    )
    rendered_components = [
        re_render_component(call_context, component_address)
        for component_address in dirty_components
    ]
    return HttpResponse("\n".join(rendered_components), headers=headers)


def clear_session(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse("Only POST allowed", status=405)
    session_id = request.GET.get("session_id")
    if not session_id:
        return HttpResponse("session_id is required", status=400)
    get_state_manager().clear_session(session_id)
    return HttpResponse("")


def parse_body(request: HttpRequest) -> dict[str, Any]:
    if request.content_type == "application/json":
        if request.body == b"":
            return {}
        return json.loads(request.body.decode())
    return request.POST.dict()


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
    context = RequestContext(
        call_context.request,
        {
            "request": call_context.request,
            "LIVECOMPONENTS_SESSION_ID": state_address.session_id,
            "full_component_id": state_address.component_id,
        },
    )
    html = call_context.state_manager.restore_component_template(state_address)
    if not html:
        raise ValueError(f"HTML for {state_address!r} not found")

    template = "{% load livecomponents component_tags %}" + html
    return Template(template).render(context)
