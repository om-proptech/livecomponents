from typing import TypeVar

from pydantic import BaseModel, ConfigDict, field_validator

from livecomponents.const import DEFAULT_OWN_ID, HIER_SEP, TYPE_SEP
from livecomponents.utils import LiveComponentsPath, get_ancestor_id

State = TypeVar("State", bound=BaseModel)


class ComponentId(str):
    def __or__(self, other: str | tuple[str, str]):
        """Return the component id of the child component.

        Can be used as this, without explicitly setting the child own_id:

            state_address.component_id | "child_component"

        Or this, with explicitly setting the child own_id:

            state_address.component_id | ("child_component", "child_own_id")

        """
        if isinstance(other, str):
            return ComponentId(f"{self}{HIER_SEP}{other}{TYPE_SEP}{DEFAULT_OWN_ID}")
        elif isinstance(other, tuple):
            return ComponentId(f"{self}{HIER_SEP}{other[0]}{TYPE_SEP}{other[1]}")
        else:
            return NotImplemented


class StateAddress(BaseModel):
    session_id: str
    component_id: ComponentId

    @field_validator("component_id", mode="before")
    @classmethod
    def validate_component_id(cls, v):
        return ComponentId(v)

    def __or__(self, other: str | tuple[str, str]):
        new_component_id = self.component_id | other
        return StateAddress(session_id=self.session_id, component_id=new_component_id)

    def with_component_id(self, component_id: str) -> "StateAddress":
        """Return a new StateAddress with the given component_id."""
        return StateAddress(
            session_id=self.session_id, component_id=ComponentId(component_id)
        )

    def find_ancestor(self, ancestor_type: str) -> "StateAddress | None":
        """Find the closest ancestor of the given type."""
        ancestor_component_id = get_ancestor_id(self.component_id, ancestor_type)
        if not ancestor_component_id:
            return None
        return StateAddress(
            session_id=self.session_id, component_id=ComponentId(ancestor_component_id)
        )

    def must_find_ancestor(self, ancestor_type: str) -> "StateAddress":
        ancestor = self.find_ancestor(ancestor_type)
        if not ancestor:
            raise ValueError(f"Ancestor {ancestor_type} not found")
        return ancestor

    def get_parent(self) -> "StateAddress | None":
        """Returns the parent of this component or None.

        Reutrn None if this component is a root component."""
        parent = LiveComponentsPath(self.component_id).parent
        if parent == LiveComponentsPath("|"):
            return None
        return StateAddress(
            session_id=self.session_id, component_id=ComponentId(parent)
        )

    def must_get_parent(self) -> "StateAddress":
        """Returns the parent of this component or raises ValueError.

        Assume that the parent exists.
        """
        parent = self.get_parent()
        if parent is None:
            raise ValueError(f"{self} has no parent")
        return parent

    def get_component_name(self):
        return LiveComponentsPath(self.component_id).stem

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)


class CallMethodRequestArgs(BaseModel):
    session_id: str
    component_id: str
    command_name: str

    def get_state_address(self) -> StateAddress:
        return StateAddress(session_id=self.session_id, component_id=self.component_id)
