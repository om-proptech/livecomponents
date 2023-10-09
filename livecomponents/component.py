import abc
from typing import Generic

from django_components import component

from livecomponents.manager import get_state_manager
from livecomponents.manager.utils import gen_random_component_id
from livecomponents.types import State


class LiveComponent(component.Component, Generic[State]):
    def get_context_data(
        self,
        parent_id: str | None = None,
        component_id: str | None = None,
        component_name: str | None = None,
        **component_kwargs,
    ):
        if component_id is None:
            component_id = gen_random_component_id()
        session_id = self.outer_context["LIVECOMPONENTS_SESSION_ID"]
        component_type = self.registered_name
        state_store = get_state_manager()
        state = state_store.get_or_create_component(
            session_id=session_id,
            component_type=component_type,
            component_id=component_id,
            parent_id=parent_id,
            component_name=component_name,
            state_constructor=self.init_state,
            component_kwargs=component_kwargs,
        )
        extra_context = self.get_extra_context_data(state)
        context = {
            **component_kwargs,
            **state.model_dump(),
            **extra_context,
            # Put "session_id" and "component_id" last to ensure they are
            # not overwritten
            "session_id": session_id,
            "component_id": component_id,
            "parent_id": parent_id,
        }
        return context

    def get_extra_context_data(self, state: State):
        """Optionally add additional context data to the component."""
        return {}

    @classmethod
    @abc.abstractmethod
    def init_state(cls, **component_kwargs) -> State:
        ...
