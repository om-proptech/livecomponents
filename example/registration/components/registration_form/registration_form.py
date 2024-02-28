from typing import Any

from django import forms
from django_components import component

from livecomponents import (
    CallContext,
    ExtraContextRequest,
    InitStateContext,
    LiveComponent,
    LiveComponentsModel,
    command,
)


class RegistrationForm(forms.Form):
    email = forms.CharField(initial="user@example.com")
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("Email is required")
        if "@" not in email:
            raise forms.ValidationError("Invalid email")
        if email.endswith("@gmail.com"):
            raise forms.ValidationError("We are not accepting gmail.com emails")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match")
        return cleaned_data


class RegistrationFormState(LiveComponentsModel):
    """State for the registration form component.

    Notice that we keep form_data, and not the entire Form instance in the state.
    We do it because the state is smaller than form, it's less likely to break on
    serialization, and this is the only state we need to keep.

    The form handling procedure goes like this:

    - First, we handle the form submission in the register() command. If the form
      happen to be invalid, we store the form data in the state.
    - Then, we re-create the form from the state in the get_extra_context_data().
      The form from get_extra_context_data() is used to render the form in the template.
    """

    user_registered: bool = False
    form_data: dict | None = None


@component.register("registration_form")
class RegistrationFormComponent(LiveComponent[RegistrationFormState]):
    template_name = "registration_form/registration_form.html"

    def get_extra_context_data(
        self, extra_context_request: ExtraContextRequest[RegistrationFormState]
    ) -> dict[str, Any]:
        """Return extra context to render the component template."""
        form_data = extra_context_request.state.form_data
        return {
            "form": RegistrationForm(data=form_data),
        }

    def init_state(self, context: InitStateContext) -> RegistrationFormState:
        return RegistrationFormState()

    @command
    def register(
        self,
        call_context: CallContext[RegistrationFormState],
        **form_data: dict,
    ):
        form = RegistrationForm(data=form_data)
        if form.is_valid():
            call_context.state.user_registered = True
            call_context.state.form_data = None
        else:
            call_context.state.user_registered = False
            call_context.state.form_data = dict(form_data)

    @command
    def try_again(self, call_context: CallContext[RegistrationFormState]):
        call_context.state.user_registered = False
        call_context.state.form_data = None
