from django_components import register
from pydantic import BaseModel

from livecomponents import CallContext, InitStateContext, LiveComponent, command


class ModalState(BaseModel):
    open: bool = False


@register("modal")
class Modal(LiveComponent[ModalState]):
    template_name = "modal/modal.html"

    def init_state(self, context: InitStateContext) -> ModalState:
        return ModalState(**context.component_kwargs)

    @command
    def close(self, call_context: CallContext[ModalState]):
        call_context.state.open = False

    @command
    def open(self, call_context: CallContext[ModalState]):
        call_context.state.open = True
