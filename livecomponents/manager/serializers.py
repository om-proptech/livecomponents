import abc
import pickle
from typing import Any


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
