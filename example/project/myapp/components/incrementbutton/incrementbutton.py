from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import CallContext, InitStateContext


class IncrementButtonState(BaseModel):
    value: int = 1
    label: str = "+"


@component.register("incrementbutton")
class IncrementButton(LiveComponent[IncrementButtonState]):
    template_name = "incrementbutton/incrementbutton.html"

    @classmethod
    def init_state(
        cls, context: InitStateContext, **component_kwargs
    ) -> IncrementButtonState:
        return IncrementButtonState(**component_kwargs)

    @classmethod
    def increment_parent_counter(
        cls, call_context: CallContext[IncrementButtonState], value: int = 1
    ):
        call_context.parent.increment(value=value)
