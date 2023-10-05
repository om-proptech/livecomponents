import abc
from typing import Generic

from django_components import component

from livecomponents.state_stores import get_default_state_store
from livecomponents.types import State


class LiveComponent(component.Component, Generic[State]):
    def get_context_data(self, component_id: str, **kwargs):
        session_id = self.outer_context["live_component_session_id"]

        state_store = get_default_state_store()
        state = state_store.get_or_create_component_state(
            session_id, component_id, self.init_state
        )
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
    @abc.abstractmethod
    def init_state(cls) -> State:
        ...
