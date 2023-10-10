from django.core.exceptions import PermissionDenied
from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import CallContext, InitStateContext


class MessageState(BaseModel):
    message: str | None = None
    initialized_from: str | None = None


@component.register("message")
class MessageComponent(LiveComponent[MessageState]):
    template_name = "message/message.html"
    state_cls = MessageState

    @classmethod
    def init_state(cls, context: InitStateContext, **component_kwargs) -> MessageState:
        initialized_from = context.request.META["REMOTE_ADDR"]

        if context.request.GET.get("forbidden"):
            raise PermissionDenied()

        return MessageState(initialized_from=initialized_from, **component_kwargs)

    @classmethod
    def set_message(cls, call_context: CallContext, message: str):
        call_context.state.message = message
