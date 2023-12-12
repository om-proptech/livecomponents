from typing import Any

from django_components import component
from pydantic import BaseModel

from livecomponents import CallContext, InitStateContext, LiveComponent, command


class EmailSenderState(BaseModel):
    pass


@component.register("emailsender")
class EmailSender(LiveComponent[EmailSenderState]):
    template_name = "emailsender/emailsender.html"

    def get_extra_context_data(
        self, state: EmailSenderState, **component_kwargs
    ) -> dict[str, Any]:
        return {}

    def init_state(
        self, context: InitStateContext, **component_kwargs
    ) -> EmailSenderState:
        return EmailSenderState()

    @command
    def send_email(self, call_context: CallContext[EmailSenderState], email: str):
        print("Sending email to", email)
