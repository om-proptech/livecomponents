import abc
import io
import pickle
import pickletools
from collections.abc import Callable
from typing import Any

from django.apps import apps
from django.db.models import Model
from django.forms import BaseForm
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
        if has_livecomponent_reducer(obj):
            logger.debug("Custom pickling: using custom reducer for %s", obj.__class__)
            return NotImplemented

        if isinstance(obj, DjangoTemplates):
            return pickle_django_templates(obj)
        if isinstance(obj, BaseForm):
            return pickle_django_form(obj)
        if isinstance(obj, BaseModel):
            return pickle_pydantic_model(obj)
        if isinstance(obj, Model):
            # This works only for unsaved models. Saved models are pickled by their pk.
            return pickle_django_model(obj)
        return NotImplemented

    def persistent_id(self, obj):
        if isinstance(obj, Model):
            if obj.pk:
                # Saved Django model.
                logger.debug(
                    "Custom pickling: Django model with persistent_id: class=%s, pk=%s",
                    obj.__class__,
                    obj.pk,
                )
                return "django_model", obj._meta.app_label, obj._meta.model_name, obj.pk
            else:
                # Unsaved Django model. Don't use persistent_id.
                logger.debug(
                    "Custom pickling: Unsaved Django model: class=%s", obj.__class__
                )
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
            try:
                return model_class.objects.get(pk=pk)
            except model_class.DoesNotExist:
                raise pickle.UnpicklingError(
                    f"Model {model_class} with pk={pk} does not exist"
                )
        raise pickle.UnpicklingError(f"Unsupported persistent id: {pid}")


def pickle_django_templates(instance: DjangoTemplates):
    """Custom pickler for DjangoTemplates renderer.

    See https://stackoverflow.com/a/77286987
    """
    logger.debug(
        "Custom pickling: DjangoTemplates renderer: class=%s", instance.__class__
    )
    return DjangoTemplates, ()


def pickle_django_form(instance: BaseForm):
    data = instance.data if instance.is_bound else None
    constructor_kwargs = {
        "initial": instance.initial,
        "data": data,
    }
    # If the form is a ModelForm, we need to store the instance separately.
    if hasattr(instance, "instance"):
        constructor_kwargs["instance"] = instance.instance
    logger.debug(
        "Custom pickling: Form with initial and data: class=%s, constructor_kwargs=%r",
        instance.__class__,
        constructor_kwargs,
    )
    return unpickle_django_form_v2, (instance.__class__, constructor_kwargs)


def unpickle_django_form(cls, initial: dict | None, data: dict | None):
    # Legacy (v1) form unpickling.
    logger.debug(
        "Custom unpickling: Form with initial and data: class=%s", cls.__name__
    )
    return cls(initial=initial, data=data)


def unpickle_django_form_v2(cls, constructor_kwargs: dict):
    logger.debug(
        "Custom unpickling: Form with constructor_kwargs: class=%s", cls.__name__
    )
    form = cls(**constructor_kwargs)
    if form.is_bound:
        form.full_clean()
    return form


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


def pickle_django_model(instance: Model):
    """Pickle Django models.

    This function pickles only unsaved models. Saved models are pickled by their
    primary key in the persistent_id method and retrieved from the database in
    persistent_load method.
    """
    logger.debug("Custom pickling: Django model: class=%s", instance.__class__)
    field_data = instance.__dict__.copy()
    field_data.pop("_state", None)
    return unpickle_django_model, (instance.__class__, field_data)


def unpickle_django_model(cls, field_data: dict):
    logger.debug("Custom unpickling: Django model: class=%s", cls.__name__)
    return cls(**field_data)


def livecomponents_reducer(func: Callable) -> Callable:
    """Mark that the reducer as to be used for pickling with LivecomponentsPickler.

    The decorator has to be applied to the `__reduce__` method of a class when we want
    to enforce its use even for the objects, for which LivecomponentsPickler
    defines a custom reducer.

    See docs/state_serialization.md for more details.
    """
    func._livecomponents_reducer = True  # type: ignore
    return func


def has_livecomponent_reducer(obj: Any) -> bool:
    """Check if the object has a custom reducer for LivecomponentsPickler."""
    return hasattr(obj, "__reduce__") and getattr(
        obj.__reduce__, "_livecomponents_reducer", False
    )
