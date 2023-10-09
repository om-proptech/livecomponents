from pathlib import PurePosixPath
from typing import TypeVar

from pydantic import BaseModel

State = TypeVar("State")


class StateAddress(BaseModel):
    session_id: str
    component_id: str

    def get_parent(self) -> "StateAddress | None":
        """Returns the parent of this component or None.

        Reutrn None if this component is a root component."""
        parent = PurePosixPath(self.component_id).parent
        if parent == PurePosixPath("/"):
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
        return PurePosixPath(self.component_id).stem

    class Config:
        frozen = True


class CallMethodRequestArgs(BaseModel):
    session_id: str
    component_id: str
    method_name: str

    def get_state_address(self) -> StateAddress:
        return StateAddress(session_id=self.session_id, component_id=self.component_id)
