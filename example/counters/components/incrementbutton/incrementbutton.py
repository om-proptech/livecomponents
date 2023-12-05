from django_components import component
from pydantic import BaseModel

from livecomponents import CallContext, InitStateContext, LiveComponent, command


class IncrementButtonState(BaseModel):
    value: int = 1
    label: str = "+"


@component.register("incrementbutton")
class IncrementButton(LiveComponent[IncrementButtonState]):
    template_name = "incrementbutton/incrementbutton.html"

    def init_state(
        self, context: InitStateContext, **component_kwargs
    ) -> IncrementButtonState:
        return IncrementButtonState(**component_kwargs)

    @command
    def increment_parent_counter(
        self, call_context: CallContext[IncrementButtonState], value: int = 1
    ):
        call_context.parent.increment(value=value)
