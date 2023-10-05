import abc
from typing import Generic

from django_components import component

from livecomponents.const import HIER_SEP, TYPE_SEP
from livecomponents.manager import get_state_manager
from livecomponents.types import State, StateAddress


def find_component_id(
    full_component_id: str | None,
    registered_name: str,
    own_id: str | None,
    parent_id: str | None = None,
) -> str:
    # Used to re-render the component
    if full_component_id is not None:
        return full_component_id

    # Used in templates
    value = registered_name
    if own_id is not None:
        value = f"{value}{TYPE_SEP}{own_id}"
    if parent_id is not None:
        value = f"{parent_id}{HIER_SEP}{value}"
    return value


class LiveComponent(component.Component, Generic[State]):
    def get_context_data(
        self,
        own_id: str | None = None,
        parent_id: str | None = None,
        full_component_id: str | None = None,
        **kwargs,
    ):
        component_id = find_component_id(
            full_component_id=full_component_id,
            registered_name=self.registered_name,
            own_id=own_id,
            parent_id=parent_id,
        )
        state_addr = StateAddress(
            session_id=self.outer_context["live_component_session_id"],
            component_id=component_id,
        )
        state_store = get_state_manager()
        state = state_store.get_or_create_component_state(state_addr, self.init_state)
        extra_context = self.get_extra_context_data(state)
        context = {
            **kwargs,
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

    @classmethod
    @abc.abstractmethod
    def init_state(cls) -> State:
        ...
