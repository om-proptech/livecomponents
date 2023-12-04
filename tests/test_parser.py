import re

from django import template
from django.template.loader import render_to_string

from livecomponents.const import HIER_SEP, TYPE_SEP
from livecomponents.manager.manager import CallContext
from livecomponents.types import StateAddress
from livecomponents.views import re_render_component

register = template.Library()


def test_parser(rf, state_manager):
    session_id = "foo"
    component_id = f"{HIER_SEP}sample{TYPE_SEP}0"  # |sample:0

    request = rf.get("/")
    rendered = render_to_string(
        "sample.html", {"var": "body", "LIVECOMPONENTS_SESSION_ID": session_id}, request
    ).strip()
    assert re.match(
        rf'<div data-livecomponent-id="{re.escape(component_id)}".*>BODYOVERRIDE</div>',
        rendered,
    )

    state_address = StateAddress(session_id=session_id, component_id=component_id)
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
        rf'<div data-livecomponent-id="{re.escape(component_id)}".*>BODYOVERRIDE</div>',
        re_rendered,
    )
