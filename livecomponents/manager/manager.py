from collections.abc import Callable
from typing import Any

from livecomponents.manager.serializers import IStateSerializer
from livecomponents.manager.stores import IStateStore


class StateManager:
    def __init__(self, serializer: IStateSerializer, store: IStateStore):
        self.serializer = serializer
        self.store = store

    def get_or_create_component_state(
        self, session_id: str, component_id: str, state_constructor: Callable[[], Any]
    ) -> Any:
        state = self.get_component_state(session_id, component_id)
        if state is None:
            state = state_constructor()
        return state

    def get_component_state(self, session_id: str, component_id: str) -> Any | None:
        raw_state = self.store.restore(session_id, component_id)
        if raw_state is None:
            return None
        return self.serializer.deserialize(raw_state)

    def set_component_state(self, session_id: str, component_id: str, state: Any):
        self.store.save(session_id, component_id, self.serializer.serialize(state))
