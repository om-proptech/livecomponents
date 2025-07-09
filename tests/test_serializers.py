import io
from pickletools import dis, genops

import pytest
from coffee.models import CoffeeBean
from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm
from pydantic import BaseModel

from livecomponents.manager.serializers import (
    PickleStateSerializer,
    livecomponents_reducer,
)


class MyModel(BaseModel):
    foo: str


class MyForm(forms.Form):
    name = forms.CharField(max_length=100)

    def clean_name(self):
        if self.cleaned_data["name"] == "BAD":
            raise forms.ValidationError("Name cannot be BAD")


class MyModelForm(ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]


def dynamic_user_form(form_fields: list[str]):
    """Dynamically create a ModelForm for the User model with specified fields."""

    class DynamicUserForm(ModelForm):
        class Meta:
            model = User
            fields = form_fields

        @livecomponents_reducer
        def __reduce__(self):
            data = self.data if self.is_bound else None
            constructor_kwargs = {
                "initial": self.initial,
                "data": data,
            }
            if hasattr(self, "instance"):
                constructor_kwargs["instance"] = self.instance
            return restore_dynamic_user_form, (form_fields, constructor_kwargs)

    return DynamicUserForm


def restore_dynamic_user_form(form_fields: list[str], constructor_kwargs: dict):
    """Restore the dynamic User form with specified fields."""
    instance = dynamic_user_form(form_fields)(**constructor_kwargs)
    instance.full_clean()
    return instance


@pytest.mark.parametrize(
    "obj, expected_arg",
    [
        (MyModel(foo="bar"), "unpickle_pydantic_model"),
        (
            MyForm(initial={"name": "foo"}, data={"name": "bar"}),
            "unpickle_django_form_v2",
        ),
        (CoffeeBean(id=1), "django_model"),
    ],
)
def test_pickle_state_serializer_pydantic_model(obj, expected_arg):
    serialized = PickleStateSerializer().serialize(obj)
    for _, arg, _ in genops(serialized):
        if arg == expected_arg:
            return
    debug = io.StringIO()
    dis(serialized, out=debug)
    raise AssertionError(
        f"Unexpected pickle result for {obj!r}\n"
        f"Dumped value:\n"
        f"{debug.getvalue()}\n"
        f"Missing opcode: {expected_arg}\n"
    )


@pytest.mark.django_db
def test_django_serialization():
    bean = CoffeeBean.objects.create(
        name="Bean", origin="Origin", roast_level="Roast", flavor_notes="Notes"
    )
    deserialized = reserialize(bean)
    assert deserialized == bean


def test_django_serialization_unsaved():
    bean = CoffeeBean(
        name="Bean", origin="Origin", roast_level="Roast", flavor_notes="Notes"
    )
    deserialized = reserialize(bean)
    assert deserialized.name == "Bean"
    assert deserialized.origin == "Origin"
    assert deserialized.roast_level == "Roast"
    assert deserialized.flavor_notes == "Notes"


def test_pydantic_serialization():
    model = MyModel(foo="bar")
    deserialized = reserialize(model)
    assert deserialized == model


def test_form_serialization():
    form = MyForm(initial={"name": "foo"}, data={"name": "bar"})
    deserialized = reserialize(form)
    assert deserialized.initial == {"name": "foo"}
    assert deserialized.data == {"name": "bar"}


def test_form_serialization_with_data():
    form = MyForm(data={"name": "bar"})
    assert form.is_bound is True

    deserialized = reserialize(form)
    assert deserialized.is_bound is True


def test_form_serialization_with_data_and_errors():
    """Deserialization should keep errors (called by full_clean)."""
    form = MyForm(data={"name": "BAD"})

    deserialized = reserialize(form)
    assert deserialized.is_bound is True
    assert deserialized.errors == {"name": ["Name cannot be BAD"]}


def test_form_serializarion_without_data():
    form = MyForm(initial={"name": "foo"})
    assert form.is_bound is False

    deserialized = reserialize(form)
    assert deserialized.is_bound is False


@pytest.mark.django_db
def test_model_form_serialization_no_instance():
    form = MyModelForm()
    deserialized = reserialize(form)
    assert deserialized.instance.pk is None


@pytest.mark.django_db
def test_model_form_serialization(admin_user):
    form = MyModelForm(instance=admin_user)
    deserialized = reserialize(form)
    assert deserialized.instance == admin_user


@pytest.mark.django_db
def test_dynamic_model_with_custom_reducer_serialization(admin_user):
    form = dynamic_user_form(form_fields=["username", "email"])(instance=admin_user)
    deserialized = reserialize(form)
    assert deserialized.fields.keys() == {"username", "email"}
    assert deserialized.instance == admin_user


def test_model_form_serialization_unsaved_instance():
    form = MyModelForm()
    form.instance.username = "foo"
    deserialized = reserialize(form)
    assert deserialized.instance.username == "foo"


def reserialize(obj):
    return PickleStateSerializer().deserialize(PickleStateSerializer().serialize(obj))
