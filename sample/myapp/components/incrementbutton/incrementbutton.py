from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import CallContext


class ZeroState(BaseModel):
    pass


@component.register("incrementbutton")
class IncrementButton(LiveComponent[ZeroState]):
    template_name = "incrementbutton/incrementbutton.html"

    @classmethod
    def init_state(cls) -> ZeroState:
        return ZeroState()

    @classmethod
    def increment_parent_counter(cls, call_context: CallContext[ZeroState]):
        parent_component_id = call_context.state_address.component_id.replace(
            "-incrementbutton", ""
        )
        call_context.state_manager.call_with_context(
            call_context,
            component_name="clickcounter",
            component_id=parent_component_id,
            method_name="increment",
        )
