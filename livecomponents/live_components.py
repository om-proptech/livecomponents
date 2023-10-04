from typing import Generic

from django_components import component

from livecomponents.state_stores import get_default_state_store
from livecomponents.types import State


class LiveComponent(component.Component, Generic[State]):
    # We need a reference to the state class to be able to instantiate it
    state_cls: type[State]

    def get_context_data(self, session_id: str, component_id: str, **kwargs):
        state_store = self.get_state_store()

        # State, restored from the store
        state = state_store.get_component_state(session_id, component_id)
        if state is None:
            state = self.init_state()

        # Extra context data, provided by the component
        extra_context = self.get_extra_context_data(state)

        context = {
            **kwargs,
            **state.model_dump(),
            **extra_context,
            # Put "session_id" and "component_id" last to ensure they are
            # not overwritten
            "session_id": session_id,
            "component_id": component_id,
        }
        return context

    def get_extra_context_data(self, state: State):
        """Optionally add additional context data to the component."""
        return {}

    @classmethod
    def init_state(cls) -> State:
        """Initialize the state of the component.

        You can override this method to provide a custom state initialization.
        """

        return cls.state_cls()

    @classmethod
    def get_state_store(cls):
        return get_default_state_store()

    @classmethod
    def get_or_create_state(cls, session_id: str, component_id: str):
        state_store = cls.get_state_store()
        state = state_store.get_component_state(session_id, component_id)
        if state is None:
            state = cls.init_state()
        return state

    @classmethod
    def save_state(cls, session_id: str, component_id: str, state: State):
        state_store = cls.get_state_store()
        state_store.set_component_state(session_id, component_id, state)
