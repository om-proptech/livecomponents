from typing import Any

import inflect
from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.const import HIER_SEP, TYPE_SEP
from livecomponents.manager.manager import CallContext

p = inflect.engine()


class ClickCounterState(BaseModel):
    value: int = 42
    title: str = ""


@component.register("clickcounter")
class ClickCounter(LiveComponent[ClickCounterState]):
    template_name = "clickcounter/clickcounter.html"

    def get_extra_context_data(self, state: ClickCounterState) -> dict[str, Any]:
        return {"value_str": p.number_to_words(state.value)}

    @classmethod
    def init_state(cls, **component_kwargs) -> ClickCounterState:
        return ClickCounterState(**component_kwargs)

    @classmethod
    def increment(cls, call_context: CallContext[ClickCounterState], value: int = 1):
        call_context.state.value += value
        call_context.state_manager.call_with_context(
            call_context,
            component_id=f"{HIER_SEP}message{TYPE_SEP}0",
            method_name="set_message",
            kwargs={
                "message": (
                    f"Counter {call_context.state.title!r} incremented "
                    f"to {value}. "
                    f"Its new value is now {call_context.state.value}."
                )
            },
        )
