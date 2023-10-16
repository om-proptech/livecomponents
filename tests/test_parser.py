import re

from django import template
from django.template.loader import render_to_string

from livecomponents.manager import get_state_manager
from livecomponents.manager.manager import CallContext
from livecomponents.types import StateAddress
from livecomponents.views import re_render_component

register = template.Library()


def test_parser(rf):
    get_state_manager().store.client.flushall()

    session_id = "foo"

    request = rf.get("/")
    rendered = render_to_string(
        "sample.html", {"var": "body", "LIVECOMPONENTS_SESSION_ID": session_id}, request
    ).strip()
    assert re.match(
        r'<div data-livecomponent-id="/sample\.0".*>BODYOVERRIDE</div>', rendered
    )

    state_manager = get_state_manager()
    state_address = StateAddress(session_id=session_id, component_id="/sample.0")
    state = state_manager.get_component_state(state_address)
    call_context = CallContext(
        request=request,
        state=state,
        state_address=state_address,
        state_manager=state_manager,
    )
    re_rendered = re_render_component(
        call_context=call_context, state_address=state_address
    ).strip()
    assert re.match(
        r'<div data-livecomponent-id="/sample\.0".*>BODYOVERRIDE</div>', re_rendered
    )
