from typing import Any

import inflect
from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import CallContext

p = inflect.engine()


class ClickCounterState(BaseModel):
    value: int = 42


@component.register("clickcounter")
class ClickCounter(LiveComponent[ClickCounterState]):
    template_name = "clickcounter/clickcounter.html"

    def get_extra_context_data(self, state: ClickCounterState) -> dict[str, Any]:
        return {"value_str": p.number_to_words(state.value)}

    @classmethod
    def init_state(cls) -> ClickCounterState:
        return ClickCounterState()

    @classmethod
    def increment(cls, call_context: CallContext[ClickCounterState]):
        call_context.state.value += 1
        call_context.state_manager.call_with_context(
            call_context,
            component_name="message",
            component_id="message-0",
            method_name="set_message",
            kwargs={
                "message": (
                    f"Counter {call_context.state_address.component_id} incremented. "
                    f"Its value is now {call_context.state.value}."
                )
            },
        )

    @classmethod
    def decrement(cls, call_context: CallContext[ClickCounterState]):
        call_context.state.value -= 1
        call_context.state_manager.call_with_context(
            call_context,
            component_name="message",
            component_id="message-0",
            method_name="set_message",
            kwargs={
                "message": (
                    f"Counter {call_context.state_address.component_id} decremented. "
                    f"Its value is now {call_context.state.value}."
                )
            },
        )
