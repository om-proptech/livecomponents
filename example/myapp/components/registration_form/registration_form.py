from django import forms
from django_components import component

from livecomponents import (
    CallContext,
    InitStateContext,
    LiveComponent,
    LiveComponentsModel,
    command,
)
from livecomponents.form_utils import populate_form_with_data


class RegistrationForm(forms.Form):
    email = forms.CharField()
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
    user_registered: bool = False
    form: RegistrationForm


@component.register("registration_form")
class RegistrationFormComponent(LiveComponent[RegistrationFormState]):
    template_name = "registration_form/registration_form.html"

    def init_state(self, context: InitStateContext) -> RegistrationFormState:
        return RegistrationFormState(
            form=RegistrationForm(initial=context.component_kwargs)
        )

    @command
    def register(
        self,
        call_context: CallContext[RegistrationFormState],
        **form_data: dict,
    ):
        form = call_context.state.form = populate_form_with_data(
            call_context.state.form, form_data
        )
        if form.is_valid():
            call_context.state.user_registered = True
        else:
            call_context.state.user_registered = False

    @command
    def try_again(self, call_context: CallContext[RegistrationFormState]):
        call_context.state.user_registered = False
        call_context.state.form = RegistrationForm()
