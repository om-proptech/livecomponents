import abc
import io
import pickle
import pickletools
from typing import Any

from django.apps import apps
from django.db.models import Model
from django.forms import Form
from django.forms.renderers import DjangoTemplates
from pydantic import BaseModel

from livecomponents.logging import logger


class IStateSerializer(abc.ABC):
    @abc.abstractmethod
    def deserialize(self, raw_state: bytes) -> Any:
        ...

    @abc.abstractmethod
    def serialize(self, state: Any) -> bytes:
        ...


class PickleStateSerializer(IStateSerializer):
    def deserialize(self, raw_state: bytes) -> Any:
        unpickler = LivecomponentsUnpickler(io.BytesIO(raw_state))
        return unpickler.load()

    def serialize(self, state: Any) -> bytes:
        buf = io.BytesIO()
        pickler = LivecomponentsPickler(buf)
        pickler.dump(state)
        optimized = pickletools.optimize(buf.getvalue())
        logger.debug("Serialized state size: %d bytes", len(optimized))
        return optimized


class LivecomponentsPickler(pickle.Pickler):
    """Pickler that supports more effective pickling of some objects.

    - For Django forms: pickle the form initial state and data. Makes it possible
      to store fewer data in the state and avoid pickling the entire form instance.
    - For Pydantic model: pickle the model's dict representation.
      When restoring the state, the model will be reconstructed from the dict, which
      makes it possible to evolve the model's fields without breaking the state.
    - For Django templates: pickle the DjangoTemplates renderer.
    - For Django models: use persistent_id to pickle the model by its primary key.
    """

    def reducer_override(self, obj):
        if isinstance(obj, DjangoTemplates):
            return pickle_django_templates(obj)
        if isinstance(obj, Form):
            return pickle_django_form(obj)
        if isinstance(obj, BaseModel):
            return pickle_pydantic_model(obj)
        return NotImplemented

    def persistent_id(self, obj):
        if isinstance(obj, Model):
            logger.debug(
                "Custom pickling: Django model with persistent_id: class=%s, pk=%s",
                obj.__class__,
                obj.pk,
            )
            return "django_model", obj._meta.app_label, obj._meta.model_name, obj.pk
        return None


class LivecomponentsUnpickler(pickle.Unpickler):
    def persistent_load(self, pid):
        type_tag, app_label, model_name, pk = pid
        if type_tag == "django_model":
            logger.debug(
                "Custom unpickling: Django model with persistent_id: "
                "app_label=%s, model_name=%s, pk=%s",
                app_label,
                model_name,
                pk,
            )
            model_class = apps.get_model(app_label, model_name)
            return model_class.objects.get(pk=pk)
        raise pickle.UnpicklingError(f"Unsupported persistent id: {pid}")


def pickle_django_templates(instance: DjangoTemplates):
    """Custom pickler for DjangoTemplates renderer.

    See https://stackoverflow.com/a/77286987
    """
    logger.debug(
        "Custom pickling: DjangoTemplates renderer: class=%s", instance.__class__
    )
    return DjangoTemplates, ()


def pickle_django_form(instance: Form):
    logger.debug(
        "Custom pickling: Form with initial and data: class=%s", instance.__class__
    )
    data = instance.data if instance.is_bound else None
    return unpickle_django_form, (instance.__class__, instance.initial, data)


def unpickle_django_form(cls, initial: dict | None, data: dict | None):
    logger.debug(
        "Custom unpickling: Form with initial and data: class=%s", cls.__name__
    )
    return cls(initial=initial, data=data)


def pickle_pydantic_model(instance: BaseModel):
    logger.debug(
        "Custom pickling: Pydantic model with model_dump: class=%s",
        instance.__class__,
    )
    return unpickle_pydantic_model, (
        instance.__class__,
        instance.model_dump(),
    )


def unpickle_pydantic_model(cls, model_dict: dict):
    logger.debug(
        "Custom unpickling: Pydantic model with model_dump: class=%s", cls.__name__
    )
    return cls(**model_dict)
