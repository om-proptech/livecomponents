from typing import TypeVar

from django.forms import BaseForm

TBaseForm = TypeVar("TBaseForm", bound=BaseForm)


def populate_form_with_data(form: TBaseForm, data: dict) -> TBaseForm:
    """Create a form copy, populated with the given data.

    Helpful when the form, received from the livecomponent state, has to be populated
    with the data, received from the client. Passing form.data = data is not enough,
    as it leaves the form in the inconsistent initial state (e.g., form.is_bound is
    False, and form errors are outdated).

    Works well with regular form without extra __init__ arguments and with model
    forms.

    Example:

        class MyFormState(LiveComponentsModel):
            form: MyForm = Field(default_factory=MyForm)

        @component.register("...")
        class MyFormComponent(LiveComponent[MyFormState]):

            @command
            def submit_form(
                self,
                call_context: CallContext[MyFormState],
                **form_data: dict,
            ):
                form = call_context.state.form = populate_form_with_data(
                    call_context.state.form, form_data
                )
                if form.is_valid():
                    # Do something with the form
                    ...
    """
    constructor_kwargs = {
        "initial": form.initial,
        "data": data,
    }
    if hasattr(form, "instance"):
        constructor_kwargs["instance"] = form.instance
    return form.__class__(**constructor_kwargs)
