import pytest
from django import forms
from django.contrib.auth.models import User

from livecomponents.form_utils import populate_form_with_data


class MyForm(forms.Form):
    name = forms.CharField()
    email = forms.EmailField()


class MyModelForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]


def test_populate_form_with_data():
    form = MyForm()
    form_data = {"name": "John", "email": "john@example.com"}
    populated_form = populate_form_with_data(form, form_data)
    assert populated_form.is_valid()
    assert populated_form.is_bound
    assert populated_form.cleaned_data == form_data


@pytest.mark.django_db
def test_populate_model_form_with_data(admin_user):
    form = MyModelForm(instance=admin_user)
    form_data = {"username": "John", "email": "john@example.com"}
    populated_form = populate_form_with_data(form, form_data)
    assert populated_form.is_valid()
    assert populated_form.is_bound
    assert populated_form.cleaned_data == form_data
    assert populated_form.instance == admin_user
