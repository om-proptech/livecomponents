from typing import Any

from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import CallContext


class ClickCounterState(BaseModel):
    value: int = 1000
    title: str = ""


@component.register("clickcounter")
class ClickCounter(LiveComponent[ClickCounterState]):
    template_name = "clickcounter/clickcounter.html"

    def get_extra_context_data(self, state: ClickCounterState) -> dict[str, Any]:
        return {"value_str": f"{state.value:,}"}

    @classmethod
    def init_state(cls, **component_kwargs) -> ClickCounterState:
        return ClickCounterState(**component_kwargs)

    @classmethod
    def increment(cls, call_context: CallContext[ClickCounterState], value: int = 1):
        call_context.state.value += value
        call_context.find_one("/message.0").set_message(
            message=(
                f"Counter {call_context.state.title!r} incremented "
                f"to {value}. "
                f"Its new value is now {call_context.state.value}."
            )
        )
