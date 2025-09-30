import json
from typing import Any

from django.core.exceptions import BadRequest
from django.http import HttpRequest, HttpResponse
from django.template import RequestContext, Template
from django.views.decorators.clickjacking import xframe_options_exempt
from django_components.component_registry import NotRegistered

from livecomponents.exceptions import CancelRendering
from livecomponents.logging import logger
from livecomponents.manager import get_state_manager
from livecomponents.manager.manager import CallContext
from livecomponents.sentry_utils import set_transaction_name, start_span
from livecomponents.settings import get_config
from livecomponents.types import CallMethodRequestArgs, StateAddress


def maybe_xframe_exempt(view_func):
    """Conditionally apply xframe_options_exempt based on settings."""
    config = get_config()
    if config.xframe_options_exempt:
        return xframe_options_exempt(view_func)
    return view_func


@maybe_xframe_exempt
def call_command(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse("Only POST allowed", status=405)
    args = CallMethodRequestArgs(**request.GET.dict())
    state_manager = get_state_manager()
    kwargs = parse_body(request)

    sentry_arg = f"[{args.component_id}].{args.command_name}"
    set_transaction_name(f"lc.call_command({sentry_arg})")
    if not state_manager.session_exists(args.session_id):
        logger.warning(
            "Session %s does not exist. It may have expired", args.session_id
        )
        return HttpResponse("Session does not exist. It may have expired", status=410)

    try:
        call_context = state_manager.call_component_command(
            request,
            args.get_state_address(),
            args.command_name,
            kwargs=kwargs,
        )
    except NotRegistered as error:
        raise BadRequest(f"Component {args.component_id} is not registered") from error

    headers = call_context.execution_results.response_headers

    if not call_context.execution_results.is_partial_render_necessary():
        # Shortcut for full page refresh
        return HttpResponse(
            headers=call_context.execution_results.response_headers,
        )

    dirty_components = deduplicate_dirty_components(
        call_context.execution_results.dirty_components
    )

    with start_span(f"re_render_components({sentry_arg})"):
        rendered_components = re_render_components(
            component_addresses=dirty_components,
            call_context=call_context,
        )
    return HttpResponse("\n".join(rendered_components), headers=headers)


@maybe_xframe_exempt
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
        try:
            return json.loads(request.body.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise BadRequest("Invalid livecomponent request body (not valid JSON)")
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


def re_render_components(
    component_addresses: set[StateAddress], call_context: CallContext
) -> list[str]:
    """Re-render components and return their HTML.

    If any of the components raises an CancelRendering() exception, then
    this component rendering is cancelled and an empty string is returned
    instead of the HTML for this component.
    """
    ret: list[str] = []
    for component_address in component_addresses:
        try:
            ret.append(re_render_component(call_context, component_address))
        except CancelRendering:
            logger.warning(
                "Component %s cancelled rendering", component_address.component_id
            )
            ret.append("")
    return ret


def re_render_component(call_context: CallContext, state_address: StateAddress) -> str:
    context = RequestContext(
        call_context.request,
        {
            "request": call_context.request,
            "LIVECOMPONENTS_SESSION_ID": state_address.session_id,
            "full_component_id": state_address.component_id,
        },
    )
    sentry_arg = f"[{state_address.component_id}]"
    with start_span(f"re_render({sentry_arg})"):
        html = call_context.state_manager.restore_component_template(state_address)
        if not html:
            error_message = (
                f"Cannot find HTML for '{state_address}'. "
                f"Did you use '{{% component ... %}}' instead of "
                f"'{{% livecomponent ... %}}' in the Django template?"
            )
            raise ValueError(error_message)

        template = "{% load livecomponents component_tags %}" + html
        return Template(template).render(context)
