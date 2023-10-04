import abc
import pickle
from typing import Any


class IStateStore(abc.ABC):
    def get_component_state(self, session_id: str, component_id: str) -> Any | None:
        raw_state = self.get_raw_component_state(session_id, component_id)
        if raw_state is None:
            return None
        return self.deserialize_state(raw_state)

    @staticmethod
    def deserialize_state(raw_state: bytes) -> Any:
        return pickle.loads(raw_state)

    @abc.abstractmethod
    def get_raw_component_state(
        self, session_id: str, component_id: str
    ) -> bytes | None:
        ...

    def set_component_state(self, session_id: str, component_id: str, state: Any):
        self.set_raw_component_state(
            session_id, component_id, self.serialize_state(state)
        )

    @staticmethod
    def serialize_state(state: Any) -> bytes:
        return pickle.dumps(state)

    @abc.abstractmethod
    def set_raw_component_state(
        self, session_id: str, component_id: str, raw_state: bytes
    ) -> None:
        ...
