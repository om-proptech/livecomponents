from django_components import register

from livecomponents import CallContext, StatelessLiveComponent, command


@register("emailsender")
class EmailSender(StatelessLiveComponent):
    template_name = "emailsender/emailsender.html"

    @command
    def send_email(self, call_context: CallContext, email: str):
        print("Sending email to", email)
