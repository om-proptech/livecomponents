from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic

from django.http import HttpRequest
from django.template import Context
from django_components.component_registry import registry
from pydantic import Field

from livecomponents.manager.execution_results import ExecutionResults
from livecomponents.manager.serializers import IStateSerializer
from livecomponents.manager.stores import IStateStore
from livecomponents.types import State, StateAddress
from livecomponents.utils import LiveComponentsModel

if TYPE_CHECKING:
    from livecomponents.component import LiveComponent

# Keys that are not serializable or don't need to be stored
# when we store component's context.
DEFAULT_CONTEXT_IGNORE_KEYS = {
    "True",
    "False",
    "None",
    "csrf_token",
    "sql_queries",
    "request",
    "user",
    "perms",
    "messages",
    "DEFAULT_MESSAGE_LEVELS",
    "block",
    "LIVECOMPONENTS_SESSION_ID",
    "debug",
    "session_id",
    "component_id",
}


class CallContext(LiveComponentsModel, Generic[State]):
    request: HttpRequest
    state: State
    state_address: StateAddress
    state_manager: "StateManager"
    execution_results: ExecutionResults = Field(default_factory=ExecutionResults)

    def find_one(self, component_id: str) -> "CallContext":
        state = self.state_manager.get_component_state(
            self.state_address.model_copy(update={"component_id": component_id})
        )
        return self.model_copy(update={"component_id": component_id, "state": state})

    @property
    def parent(self) -> "CallContext":
        return self.find_one(self.state_address.must_get_parent().component_id)

    def __getattr__(self, command_name: str):
        """This is called when a method is called on the CallContext."""

        def call(**kwargs):
            self.state_manager.call_with_context(
                self,
                component_id=self.component_id,
                command_name=command_name,
                kwargs=kwargs,
            )

        return call


class InitStateContext(LiveComponentsModel):
    request: HttpRequest
    outer_context: Context = Field(default_factory=Context)


class StateManager:
    def __init__(self, serializer: IStateSerializer, store: IStateStore):
        self.serializer = serializer
        self.store = store

    def save_component_template(self, state_addr: StateAddress, html: str):
        self.store.save_component_template(state_addr, html.encode("utf-8"))

    def restore_component_template(self, state_addr: StateAddress) -> str | None:
        html_bytes = self.store.restore_component_template(state_addr)
        if html_bytes:
            return html_bytes.decode("utf-8")
        return None

    def get_or_create_component_state(
        self,
        request: HttpRequest,
        state_addr: StateAddress,
        state_constructor: Callable[..., Any],
        outer_context: Context,
        component_kwargs: dict[str, Any],
    ) -> tuple[Any, bool]:
        state = self.get_component_state(state_addr)
        if state is not None:
            return state, False

        init_state_context = InitStateContext(
            request=request, outer_context=outer_context
        )
        state = state_constructor(init_state_context, **component_kwargs)
        self.set_component_state(state_addr, state)
        self.set_component_context(state_addr, outer_context)
        return state, True

    def get_component_state(self, state_addr: StateAddress) -> Any | None:
        raw_state = self.store.restore_state(state_addr)
        if raw_state is None:
            return None
        return self.serializer.deserialize(raw_state)

    def set_component_state(self, state_addr: StateAddress, state: Any):
        self.store.save_state(state_addr, self.serializer.serialize(state))

    def get_component_context(self, state_addr: StateAddress) -> dict[str, Any]:
        raw_context = self.store.restore_context(state_addr)
        if raw_context is None:
            return {}
        flat_context = self.serializer.deserialize(raw_context)
        return flat_context

    def set_component_context(self, state_addr: StateAddress, context: Context):
        flat_context = dict(context.flatten())
        filtered_context = self.filter_flat_context(flat_context)
        if filtered_context:
            self.store.save_context(
                state_addr, self.serializer.serialize(filtered_context)
            )

    def filter_flat_context(self, flat_context: dict[str, Any]) -> dict[str, Any]:
        """Remove keys that are not serializable or don't need to be stored."""
        return {
            key: value
            for key, value in flat_context.items()
            if key not in DEFAULT_CONTEXT_IGNORE_KEYS and not key.startswith("_")
        }

    def get_component_class(self, component_name: str) -> type["LiveComponent"]:
        return registry.get(component_name)

    def call_component_method(
        self,
        request: HttpRequest,
        state_addr: StateAddress,
        command_name: str,
        kwargs: dict[str, Any] | None = None,
    ) -> CallContext:
        component_cls = self.get_component_class(state_addr.get_component_name())
        component_instance = component_cls()

        state = self.get_component_state(state_addr)
        if state is None:
            raise ValueError(f"Component state not found: {state_addr}")

        command = component_instance.get_command(command_name)
        call_context: CallContext = CallContext(
            request=request,
            state=state,
            state_address=state_addr,
            state_manager=self,
        )
        returned_value = command(call_context, **(kwargs or {}))
        call_context.execution_results.process_returned_value(
            state_addr, returned_value
        )
        self.set_component_state(state_addr, state)
        return call_context

    def call_with_context(
        self,
        call_context: CallContext,
        component_id: str,
        command_name: str,
        kwargs: dict[str, Any] | None = None,
    ):
        state_addr = call_context.state_address.model_copy(
            update={"component_id": component_id}
        )
        component_cls = self.get_component_class(state_addr.get_component_name())
        component_instance = component_cls()

        state = self.get_component_state(state_addr)
        if state is None:
            raise ValueError(f"Component state not found: {state_addr}")
        command = component_instance.get_command(command_name)
        updated_call_context: CallContext = CallContext(
            request=call_context.request,
            state=state,
            state_address=state_addr,
            state_manager=self,
            execution_results=call_context.execution_results,
        )

        returned_value = command(updated_call_context, **(kwargs or {}))
        updated_call_context.execution_results.process_returned_value(
            state_addr, returned_value
        )

        self.set_component_state(state_addr, state)

    def clear_session(self, session_id: str):
        self.store.clear_session(session_id=session_id)
