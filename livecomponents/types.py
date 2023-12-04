from typing import TypeVar

from pydantic import BaseModel, ConfigDict

from livecomponents.utils import LiveComponentsPath

State = TypeVar("State")


class StateAddress(BaseModel):
    session_id: str
    component_id: str

    def get_parent(self) -> "StateAddress | None":
        """Returns the parent of this component or None.

        Reutrn None if this component is a root component."""
        parent = LiveComponentsPath(self.component_id).parent
        if parent == LiveComponentsPath("|"):
            return None
        return StateAddress(session_id=self.session_id, component_id=str(parent))

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

    model_config = ConfigDict(frozen=True)


class CallMethodRequestArgs(BaseModel):
    session_id: str
    component_id: str
    command_name: str

    def get_state_address(self) -> StateAddress:
        return StateAddress(session_id=self.session_id, component_id=self.component_id)
