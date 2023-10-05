from typing import Any

import inflect
from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent

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
    def increment(cls, state: ClickCounterState):
        state.value += 1

    @classmethod
    def decrement(cls, state: ClickCounterState):
        state.value -= 1
