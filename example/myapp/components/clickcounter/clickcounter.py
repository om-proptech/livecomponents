from typing import Any

from django_components import component
from pydantic import BaseModel

from livecomponents import (
    CallContext,
    ExtraContextRequest,
    InitStateContext,
    LiveComponent,
    command,
)
from livecomponents.const import HIER_SEP, TYPE_SEP


class ClickCounterState(BaseModel):
    value: int = 1000
    title: str = ""


@component.register("clickcounter")
class ClickCounter(LiveComponent[ClickCounterState]):
    template_name = "clickcounter/clickcounter.html"

    def get_extra_context_data(
        self, extra_context_request: ExtraContextRequest[ClickCounterState]
    ) -> dict[str, Any]:
        return {"value_str": f"{extra_context_request.state.value:,}"}

    def init_state(self, context: InitStateContext) -> ClickCounterState:
        return ClickCounterState(**context.component_kwargs)

    @command
    def increment(self, call_context: CallContext[ClickCounterState], value: int = 1):
        call_context.state.value += value
        call_context.find_one(f"{HIER_SEP}message{TYPE_SEP}0").set_message(
            message=(
                f"Counter {call_context.state.title!r} incremented "
                f"by {value}. "
                f"Its new value is now {call_context.state.value}."
            )
        )
