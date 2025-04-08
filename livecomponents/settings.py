from typing import Generic, TypeVar

from django.conf import settings
from django.utils.module_loading import import_string
from pydantic import BaseModel, Field

from livecomponents.manager import StateManager
from livecomponents.manager.serializers import IStateSerializer
from livecomponents.manager.stores import IStateStore

T = TypeVar("T")


class ClassConfig(BaseModel, Generic[T]):
    """Class configuration"""

    cls: str
    config: dict = Field(default_factory=dict)

    def get_instance(self, **kwargs) -> T:
        return import_string(self.cls)(**self.config, **kwargs)


class CreateLiveComponentConfig(BaseModel):
    base_class: str = "livecomponents.LiveComponent"
    stateless_base_class: str = "livecomponents.StatelessLiveComponent"


class LivecomponentsConfig(BaseModel):
    """Configuration for livecomponents.

    Initialized by the variable LIVECOMPONENTS in Django settings.
    """

    state_serializer: ClassConfig[IStateSerializer] = Field(
        default_factory=lambda: ClassConfig(
            cls="livecomponents.manager.serializers.PickleStateSerializer"
        )
    )

    state_store: ClassConfig[IStateStore] = Field(
        default_factory=lambda: ClassConfig(
            cls="livecomponents.manager.stores.RedisStateStore"
        )
    )

    state_manager: ClassConfig[StateManager] = Field(
        default_factory=lambda: ClassConfig(
            cls="livecomponents.manager.manager.StateManager"
        )
    )

    createlivecomponent: CreateLiveComponentConfig = CreateLiveComponentConfig()

    xframe_options_exempt: bool = Field(
        default=False,
        description=(
            "If True, wraps the livecomponents views with xframe_options_exempt "
            "decorator. This allows the views to be embedded in iframes. "
        ),
    )


def get_config():
    return LivecomponentsConfig(**getattr(settings, "LIVECOMPONENTS", {}))
