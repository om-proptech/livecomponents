from typing import Generic

from django_components import component

from livecomponents.state_stores import get_default_state_store
from livecomponents.types import State


class LiveComponent(component.Component, Generic[State]):
    # We need a reference to the state class to be able to instantiate it
    state_cls: type[State]

    def get_context_data(self, session_id: str, id: str, **kwargs):
        state_store = self.get_state_store()

        # State, restored from the store
        state = state_store.get_component_state(session_id, id)
        if state is None:
            state = self.init_state()

        # Extra context data, provided by the component
        extra_context = self.get_extra_context_data(state)

        context = {
            **kwargs,
            **state.model_dump(),
            **extra_context,
            # Put "session_id" and "id" last to ensure they are not overwritten
            "session_id": session_id,
            "id": id,
        }
        return context

    def get_extra_context_data(self, state: State):
        """Optionally add additional context data to the component."""
        return {}

    def init_state(self) -> State:
        """Initialize the state of the component.

        You can override this method to provide a custom state initialization.
        """

        return self.state_cls()

    @staticmethod
    def get_state_store():
        return get_default_state_store()
