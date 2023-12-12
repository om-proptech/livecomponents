from typing import Any

from django_components import component
from pydantic import BaseModel

from livecomponents import CallContext, InitStateContext, LiveComponent, command


class ModalState(BaseModel):
    open: bool = False


@component.register("modal")
class Modal(LiveComponent[ModalState]):
    template_name = "modal/modal.html"

    def get_extra_context_data(
        self, state: ModalState, **component_kwargs
    ) -> dict[str, Any]:
        return {}

    def init_state(self, context: InitStateContext, **component_kwargs) -> ModalState:
        return ModalState(**component_kwargs)

    @command
    def close(self, call_context: CallContext[ModalState]):
        call_context.state.open = False

    @command
    def open(self, call_context: CallContext[ModalState]):
        call_context.state.open = True
