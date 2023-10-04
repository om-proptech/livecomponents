from typing import TypeVar

from pydantic import BaseModel

State = TypeVar("State", bound=BaseModel)
