import abc
from typing import Generic

from django_components import component

from livecomponents.manager import get_state_manager
from livecomponents.manager.manager import InitStateContext
from livecomponents.types import State, StateAddress
from livecomponents.utils import find_component_id

DEFAULT_OWN_ID = "0"
DEFAULT_PARENT_ID = ""


class LiveComponent(component.Component, Generic[State]):
    def get_context_data(
        self,
        own_id: str = DEFAULT_OWN_ID,
        parent_id: str = DEFAULT_PARENT_ID,
        full_component_id: str | None = None,
        **component_kwargs,
    ):
        # Fetch some data from the outer context
        session_id = self.outer_context["LIVECOMPONENTS_SESSION_ID"]
        request = self.outer_context["request"]

        component_id = find_component_id(
            full_component_id=full_component_id,
            component_name=self.registered_name,
            own_id=own_id,
            parent_id=parent_id,
        )
        state_addr = StateAddress(
            session_id=session_id,
            component_id=component_id,
        )
        state_store = get_state_manager()
        state = state_store.get_or_create_component_state(
            request,
            state_addr,
            self.init_state,
            self.outer_context,
            component_kwargs,
        )
        extra_context = self.get_extra_context_data(state)
        context = {
            **component_kwargs,
            **state.model_dump(),
            **extra_context,
            # Put "session_id" and "component_id" last to ensure they are
            # not overwritten
            **state_addr.model_dump(),
        }
        return context

    def get_extra_context_data(self, state: State):
        """Optionally add additional context data to the component."""
        return {}

    @abc.abstractmethod
    def init_state(self, context: InitStateContext, **component_kwargs) -> State:
        ...
