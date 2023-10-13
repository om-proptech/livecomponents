import abc
import copyreg
import pickle
from typing import Any

from django.forms.renderers import DjangoTemplates


class IStateSerializer(abc.ABC):
    @abc.abstractmethod
    def deserialize(self, raw_state: bytes) -> Any:
        ...

    @abc.abstractmethod
    def serialize(self, state: Any) -> bytes:
        ...


class PickleStateSerializer(IStateSerializer):
    def deserialize(self, raw_state: bytes) -> Any:
        return pickle.loads(raw_state)

    def serialize(self, state: Any) -> bytes:
        return pickle.dumps(state)


def pickle_django_templates(instance):
    return DjangoTemplates, ()


# Register a custom handler for pickling DjangoTemplates renderer
# See https://stackoverflow.com/a/77286987
copyreg.pickle(DjangoTemplates, pickle_django_templates)
