from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import CallContext


class MessageState(BaseModel):
    message: str | None = None


@component.register("message")
class MessageComponent(LiveComponent[MessageState]):
    template_name = "message/message.html"
    state_cls = MessageState

    @classmethod
    def init_state(cls, **component_kwargs) -> MessageState:
        return MessageState(**component_kwargs)

    @classmethod
    def set_message(cls, call_context: CallContext, message: str):
        call_context.state.message = message
