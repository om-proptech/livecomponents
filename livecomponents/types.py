from typing import TypeVar

from pydantic import BaseModel

from livecomponents.const import HIER_SEP

State = TypeVar("State")


class ComponentAddress(BaseModel):
    name: str
    state_address: "StateAddress"

    class Config:
        frozen = True


class StateAddress(BaseModel):
    session_id: str
    component_id: str

    def get_parent(self) -> "StateAddress | None":
        """Returns the parent of this component or None.

        Reutrn None if this component is a root component."""
        if HIER_SEP not in self.component_id:
            return None
        parent_id = self.component_id.rsplit(HIER_SEP, 1)[0]
        return StateAddress(session_id=self.session_id, component_id=parent_id)

    def must_get_parent(self) -> "StateAddress":
        """Returns the parent of this component or raises ValueError.

        Assume that the parent exists.
        """
        parent = self.get_parent()
        if parent is None:
            raise ValueError(f"{self} has no parent")
        return parent

    class Config:
        frozen = True


class CallMethodRequestArgs(BaseModel):
    component_name: str
    session_id: str
    component_id: str
    method_name: str

    def get_state_address(self) -> StateAddress:
        return StateAddress(session_id=self.session_id, component_id=self.component_id)
