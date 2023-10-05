from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic

from django.http import HttpRequest
from django_components.component_registry import registry
from pydantic import BaseModel, Field

from livecomponents.manager.serializers import IStateSerializer
from livecomponents.manager.stores import IStateStore
from livecomponents.types import ComponentAddress, State, StateAddress

if TYPE_CHECKING:
    from livecomponents.live_components import LiveComponent


class CallContext(BaseModel, Generic[State]):
    request: HttpRequest
    state: State
    component_name: str
    state_address: StateAddress
    state_manager: "StateManager"
    dirty_components: set[ComponentAddress] = Field(default_factory=set)

    def mark_as_dirty(self):
        self.dirty_components.add(
            ComponentAddress(name=self.component_name, state_address=self.state_address)
        )

    class Config:
        arbitrary_types_allowed = True


class StateManager:
    def __init__(self, serializer: IStateSerializer, store: IStateStore):
        self.serializer = serializer
        self.store = store

    def get_or_create_component_state(
        self, state_addr: StateAddress, state_constructor: Callable[[], Any]
    ) -> Any:
        state = self.get_component_state(state_addr)
        if state is None:
            state = state_constructor()
        return state

    def get_component_state(self, state_addr: StateAddress) -> Any | None:
        raw_state = self.store.restore(state_addr)
        if raw_state is None:
            return None
        return self.serializer.deserialize(raw_state)

    def set_component_state(self, state_addr: StateAddress, state: Any):
        self.store.save(state_addr, self.serializer.serialize(state))

    def get_component_class(self, component_name: str) -> type["LiveComponent"]:
        return registry.get(component_name)

    def call_component_method(
        self,
        request: HttpRequest,
        component_name: str,
        state_addr: StateAddress,
        method_name: str,
        kwargs: dict[str, Any] | None = None,
    ) -> CallContext:
        component_cls = self.get_component_class(component_name)
        state = self.get_or_create_component_state(state_addr, component_cls.init_state)
        method = getattr(component_cls, method_name)

        call_context: CallContext = CallContext(
            request=request,
            component_name=component_name,
            state=state,
            state_address=state_addr,
            state_manager=self,
        )
        method(call_context, **(kwargs or {}))
        call_context.mark_as_dirty()
        self.set_component_state(state_addr, state)
        return call_context

    def call_with_context(
        self,
        call_context: CallContext,
        component_name: str,
        component_id: str,
        method_name: str,
        kwargs: dict[str, Any] | None = None,
    ):
        component_cls = self.get_component_class(component_name)
        state_addr = call_context.state_address.model_copy(
            update={"component_id": component_id}
        )
        state = self.get_or_create_component_state(state_addr, component_cls.init_state)
        method = getattr(component_cls, method_name)
        updated_call_context: CallContext = CallContext(
            request=call_context.request,
            component_name=component_name,
            state=state,
            state_address=state_addr,
            state_manager=self,
            dirty_components=call_context.dirty_components,
        )

        # We need to pass dirty_components by reference (and not copy it)
        # so that every method call can populate it. For some reason, when
        # passing it as a constructor argument to CallContext, it gets copied,
        # so we explicitly update it here.
        updated_call_context.dirty_components = call_context.dirty_components

        method(updated_call_context, **(kwargs or {}))
        updated_call_context.mark_as_dirty()
        self.set_component_state(state_addr, state)
