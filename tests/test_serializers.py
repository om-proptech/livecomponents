import io
from pickletools import dis, genops

import pytest
from coffee.models import CoffeeBean
from django import forms
from pydantic import BaseModel

from livecomponents.manager.serializers import PickleStateSerializer


class MyModel(BaseModel):
    foo: str


class MyForm(forms.Form):
    name = forms.CharField(max_length=100)


@pytest.mark.parametrize(
    "obj, expected_arg",
    [
        (MyModel(foo="bar"), "unpickle_pydantic_model"),
        (MyForm(initial={"name": "foo"}, data={"name": "bar"}), "unpickle_django_form"),
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


def test_form_serializarion_without_data():
    form = MyForm(initial={"name": "foo"})
    assert form.is_bound is False

    deserialized = reserialize(form)
    assert deserialized.is_bound is False


def reserialize(obj):
    return PickleStateSerializer().deserialize(PickleStateSerializer().serialize(obj))
