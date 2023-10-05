from collections.abc import Callable
from typing import Any

from livecomponents.manager.serializers import IStateSerializer
from livecomponents.manager.stores import IStateStore
from livecomponents.types import StateAddress


class StateManager:
    def __init__(self, serializer: IStateSerializer, store: IStateStore):
        self.serializer = serializer
        self.store = store

    def get_or_create_component_state(
        self, state_addr: StateAddress, state_constructor: Callable[[], Any]
    ) -> Any:
        state = self.get_component_state(state_addr)
        if state is None:
            state = state_constructor()
        return state

    def get_component_state(self, state_addr: StateAddress) -> Any | None:
        raw_state = self.store.restore(state_addr)
        if raw_state is None:
            return None
        return self.serializer.deserialize(raw_state)

    def set_component_state(self, state_addr: StateAddress, state: Any):
        self.store.save(state_addr, self.serializer.serialize(state))
