from typing import TypeVar

from pydantic import BaseModel

State = TypeVar("State")


class ComponentAddress(BaseModel):
    name: str
    state_address: "StateAddress"

    class Config:
        frozen = True


class StateAddress(BaseModel):
    session_id: str
    component_id: str

    class Config:
        frozen = True


class CallMethodRequestArgs(BaseModel):
    component_name: str
    session_id: str
    component_id: str
    method_name: str

    def get_state_address(self) -> StateAddress:
        return StateAddress(session_id=self.session_id, component_id=self.component_id)
