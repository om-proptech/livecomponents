from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic

from django.http import HttpRequest
from django_components.component_registry import registry
from pydantic import BaseModel, Field

from livecomponents.manager.serializers import IStateSerializer
from livecomponents.manager.stores import IHierarchyStore, IStateStore
from livecomponents.types import State, StateAddress

if TYPE_CHECKING:
    from livecomponents.component import LiveComponent


class CallContext(BaseModel, Generic[State]):
    request: HttpRequest
    state: State
    state_address: StateAddress
    state_manager: "StateManager"
    dirty_components: set[StateAddress] = Field(default_factory=set)

    def mark_as_dirty(self):
        self.dirty_components.add(self.state_address)

    class Config:
        arbitrary_types_allowed = True

    def __getattr__(self, method_name: str):
        """This is called when a method is called on the CallContext."""

        def call(**kwargs):
            self.state_manager.call_with_context(
                self,
                component_id=self.component_id,
                method_name=method_name,
                kwargs=kwargs,
            )

        return call

    def find_one(self, component_id: str) -> "CallContext":
        state = self.state_manager.get_component_state(
            self.state_address.model_copy(update={"component_id": component_id})
        )
        return self.model_copy(update={"component_id": component_id, "state": state})

    def find_by_name(self, component_name: str) -> "CallContext":
        component_id = self.state_manager.hierarchy_store.get_by_component_name(
            self.state_address.session_id, component_name
        )
        if not component_id:
            raise ValueError(f"Component with name {component_name!r} not found")
        return self.find_one(component_id)

    @property
    def parent(self) -> "CallContext":
        parent_id = self.state_manager.hierarchy_store.get_parent(
            self.state_address.session_id, self.state_address.component_id
        )
        if not parent_id:
            raise ValueError(
                f"Component {self.state_address.component_id!r} has no parent"
            )
        return self.find_one(parent_id)


class StateManager:
    def __init__(
        self,
        serializer: IStateSerializer,
        store: IStateStore,
        hierarchy_store: IHierarchyStore,
    ):
        self.serializer = serializer
        self.store = store
        self.hierarchy_store = hierarchy_store

    def get_or_create_component(
        self,
        session_id: str,
        component_type: str,
        component_id: str,
        parent_id: str | None,
        component_name: str | None,
        state_constructor: Callable[..., Any],
        component_kwargs: dict[str, Any],
    ) -> Any:
        state_addr = StateAddress(session_id=session_id, component_id=component_id)
        state = self.get_component_state(state_addr)
        if state is None:
            state = state_constructor(**component_kwargs)
            self.set_component_state(state_addr, state)
            self.hierarchy_store.init_component(
                session_id=session_id,
                component_type=component_type,
                component_id=component_id,
                parent_id=parent_id,
                component_name=component_name,
            )
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
        state_addr: StateAddress,
        method_name: str,
        kwargs: dict[str, Any] | None = None,
    ) -> CallContext:
        component_type = self.hierarchy_store.get_component_type(
            state_addr.session_id, state_addr.component_id
        )
        component_cls = self.get_component_class(component_type)
        state = self.get_component_state(state_addr)
        if state is None:
            raise ValueError(f"Component state not found: {state_addr}")
        method = getattr(component_cls, method_name)

        call_context: CallContext = CallContext(
            request=request,
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
        component_id: str,
        method_name: str,
        kwargs: dict[str, Any] | None = None,
    ):
        state_addr = call_context.state_address.model_copy(
            update={"component_id": component_id}
        )
        component_type = self.hierarchy_store.get_component_type(
            state_addr.session_id, state_addr.component_id
        )
        component_cls = self.get_component_class(component_type)

        state = self.get_component_state(state_addr)
        if state is None:
            raise ValueError(f"Component state not found: {state_addr}")
        method = getattr(component_cls, method_name)
        updated_call_context: CallContext = CallContext(
            request=call_context.request,
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
