import abc
from typing import Generic

from django_components import component

from livecomponents.const import HIER_SEP, TYPE_SEP
from livecomponents.manager import get_state_manager
from livecomponents.types import State, StateAddress

DEFAULT_OWN_ID = "0"
DEFAULT_PARENT_ID = ""


def find_component_id(
    full_component_id: str | None,
    component_name: str,
    own_id: str,
    parent_id: str,
) -> str:
    """Generate component ID from the given parameters.

    If full_component_id is given, it is returned as-is.

    If not.

    Then, we use registered_name (a component name) and own ID (a component ID)
    to generate the "basename for the component ID" (e.g., "button.1").

    Finally, we use parent_id (a component ID) and the basename to generate
    the full component ID (e.g., "/form.0/button.1").
    """
    # Used to re-render the component
    if full_component_id is not None:
        if not full_component_id.startswith(HIER_SEP):
            raise ValueError(f"full_component_id must start with '{HIER_SEP}'")
        return full_component_id

    # Used to render the component for the first time
    basename = f"{component_name}{TYPE_SEP}{own_id}"
    return f"{parent_id}{HIER_SEP}{basename}"


class LiveComponent(component.Component, Generic[State]):
    def get_context_data(
        self,
        own_id: str = DEFAULT_OWN_ID,
        parent_id: str = DEFAULT_PARENT_ID,
        full_component_id: str | None = None,
        **component_kwargs,
    ):
        component_id = find_component_id(
            full_component_id=full_component_id,
            component_name=self.registered_name,
            own_id=own_id,
            parent_id=parent_id,
        )
        state_addr = StateAddress(
            session_id=self.outer_context["LIVECOMPONENTS_SESSION_ID"],
            component_id=component_id,
        )
        state_store = get_state_manager()
        state = state_store.get_or_create_component_state(
            state_addr, self.init_state, component_kwargs
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

    @classmethod
    @abc.abstractmethod
    def init_state(cls, **component_kwargs) -> State:
        ...
