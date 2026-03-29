from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic

from django.http import HttpRequest
from django.template import Context
from django_components.component_registry import registry
from pydantic import Field

from livecomponents.logging import logger
from livecomponents.manager.execution_results import ExecutionResults
from livecomponents.manager.serializers import IStateSerializer
from livecomponents.manager.stores import IStateStore
from livecomponents.sentry_utils import set_span_data, start_span
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
    "request",
    "LIVECOMPONENTS_SESSION_ID",
}


class CallContext(LiveComponentsModel, Generic[State]):
    """Passed to every `@command` method as the first argument (after `self`).

    Provides access to the component's state and lets you navigate to other
    components in the hierarchy.

    You can call any command on another component by chaining navigation with
    a method call. For example, `call_context.parent.set_message("Hello")`
    executes the `set_message` command on the parent component. This works
    because `find_one()`, `find_ancestor()`, and `parent` each return a new
    `CallContext`, and any unknown attribute access on a `CallContext` is
    dispatched as a command call on that component.

    Attributes:
        request: The Django request that triggered the command.
        state: The component's current state. Modify it directly; the library
            saves it after the command returns.
        state_address: The component's session ID and component ID.
        state_manager: The StateManager instance. Rarely needed directly; prefer
            `find_one()`, `find_ancestor()`, or `parent` instead.
        execution_results: Internal bookkeeping. Tracks which components need
            re-rendering after the command runs. You should not need to access
            this directly; return execution results from your command instead.
    """

    request: HttpRequest
    state: State
    state_address: StateAddress
    state_manager: "StateManager"
    execution_results: ExecutionResults = Field(default_factory=ExecutionResults)

    def find_one(self, component_id: str) -> "CallContext":
        """Return a CallContext for the component with the given ID.

        Call command methods on the result to execute them on the target
        component. For example: `call_context.find_one("|message:0").set_message("Hi")`.
        """
        state = self.state_manager.get_component_state(
            self.state_address.model_copy(update={"component_id": component_id})
        )
        return self.model_copy(update={"component_id": component_id, "state": state})

    def find_ancestor(self, ancestor_type: str) -> "CallContext":
        """Find the closest ancestor of the given type in the hierarchy."""
        ancestor = self.state_address.must_find_ancestor(ancestor_type)
        ancestor_state = self.state_manager.get_component_state(ancestor)
        return self.model_copy(
            update={"component_id": ancestor.component_id, "state": ancestor_state}
        )

    @property
    def parent(self) -> "CallContext":
        """Shortcut for the immediate parent component's CallContext."""
        return self.find_one(self.state_address.must_get_parent().component_id)

    def __getattr__(self, command_name: str):
        """Dispatch unknown attribute access as a command call on this component.

        This is the mechanism behind `call_context.parent.set_message("Hello")`.
        `parent` returns a `CallContext` for the parent component, and
        `.set_message("Hello")` hits `__getattr__`, which executes the
        `set_message` command on that parent with `{"message": "Hello"}` as kwargs.
        """

        def call(**kwargs):
            self.state_manager.call_with_context(
                self,
                component_id=self.component_id,
                command_name=command_name,
                kwargs=kwargs,
            )

        return call


class InitStateContext(LiveComponentsModel):
    """Passed to `init_state()` on a component's first render.

    Attributes:
        request: The current Django request.
        state_addr: The component's StateAddress (session ID + component ID).
        state_manager: The StateManager instance. Useful for reading another
            component's state — call `state_manager.get_component_state(addr)`.
        component_kwargs: Keyword arguments from the template tag. For example,
            `{{% livecomponent "alert" message="Hello" %}}` yields
            `{{"message": "Hello"}}`.
        outer_context: The Django template context of the page that rendered
            this component. Only available during the first render. Read page-level
            variables here and store them in state if the component needs them
            on re-render. See [On Storing Raw HTML Templates](templates.md) for
            an example.
    """

    request: HttpRequest
    state_addr: StateAddress
    state_manager: "StateManager"
    component_kwargs: dict[str, Any]
    outer_context: Context = Field(default_factory=Context)


class UpdateStateContext(LiveComponentsModel, Generic[State]):
    """Passed to `update_state()` when an already-initialized component re-renders.

    Has the same fields as `InitStateContext` plus `state` — the existing
    state loaded from Redis.

    Attributes:
        request: The current Django request.
        state_addr: The component's StateAddress (session ID + component ID).
        state_manager: The StateManager instance.
        component_kwargs: Keyword arguments from the template tag. Empty when
            the component re-renders from its own command.
        outer_context: The Django template context of the containing page.
            See `InitStateContext.outer_context` for details.
        state: The component's existing state. Modify it in place.
    """

    request: HttpRequest
    state_addr: StateAddress
    state_manager: "StateManager"
    component_kwargs: dict[str, Any]
    outer_context: Context = Field(default_factory=Context)
    state: State


class StateManager:
    """Manages component state persistence and command execution.

    Most of the time you interact with StateManager indirectly — through
    `CallContext` methods like `find_one()` or `parent`. The two methods
    useful in component code are:

    - `get_component_state(state_addr)` — load another component's state.
    - `set_component_state(state_addr, state)` — save another component's state.

    These are handy in `get_extra_context_data()` of stateless components
    that need to read their root component's state.
    """

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

    def session_exists(self, session_id: str) -> bool:
        return self.store.session_exists(session_id)

    def ensure_session(self, session_id: str) -> None:
        """Ensure the session is registered in the store.

        Called during initial render so that even pages with only stateless
        components have a discoverable session.
        """
        self.store.ensure_session(session_id)

    def component_initialized(self, state_addr: StateAddress) -> bool:
        return self.store.component_initialized(state_addr)

    def get_or_create_component_state(
        self,
        request: HttpRequest,
        state_addr: StateAddress,
        init_state: Callable[..., Any],
        update_state: Callable[..., Any],
        outer_context: Context,
        component_kwargs: dict[str, Any],
    ) -> Any:
        state = self.get_component_state(state_addr)
        if state is not None:
            update_state_context: UpdateStateContext = UpdateStateContext(
                request=request,
                state=state,
                state_addr=state_addr,
                state_manager=self,
                component_kwargs=component_kwargs,
                outer_context=outer_context,
            )
            update_state(update_state_context)
            self.set_component_state(state_addr, state)
            return state

        init_state_context = InitStateContext(
            request=request,
            state_addr=state_addr,
            state_manager=self,
            component_kwargs=component_kwargs,
            outer_context=outer_context,
        )
        state = init_state(init_state_context)
        self.set_component_state(state_addr, state)
        return state

    def get_component_state(self, state_addr: StateAddress) -> Any | None:
        """Load a component's state from Redis by its StateAddress.

        Returns None if the component has not been initialized yet.
        """
        raw_state = self.store.restore_state(state_addr)
        if raw_state is None:
            return None
        state = self.serializer.deserialize(raw_state)
        logger.debug("Getting component state for %r: %r", state_addr, state)
        return state

    def set_component_state(self, state_addr: StateAddress, state: Any):
        """Save a component's state to Redis."""
        logger.debug(
            "Setting component state for %r: %r", state_addr.component_id, state
        )
        self.store.save_state(state_addr, self.serializer.serialize(state))

    def get_component_context(self, state_addr: StateAddress) -> dict[str, Any]:
        raw_context = self.store.restore_context(state_addr)
        if raw_context is None:
            logger.debug(
                "Getting component context for %r: not found", state_addr.component_id
            )
            return {}
        flat_context = self.serializer.deserialize(raw_context)
        logger.debug(
            "Getting component context for %r: %r",
            state_addr.component_id,
            flat_context,
        )
        return flat_context

    def set_component_context(self, state_addr: StateAddress, context: dict[str, Any]):
        filtered_context = self.filter_flat_context(context)
        if filtered_context:
            logger.debug(
                "Setting component context for %s: %r",
                state_addr.component_id,
                filtered_context,
            )
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

    def call_component_command(
        self,
        request: HttpRequest,
        state_addr: StateAddress,
        command_name: str,
        kwargs: dict[str, Any] | None = None,
    ) -> CallContext:
        component_cls = self.get_component_class(state_addr.get_component_name())
        component_instance = component_cls()

        sentry_arg = f"{component_instance.get_name()}.{command_name}"
        with start_span(f"call_component_command({sentry_arg})"):
            set_span_data(
                lc_component_id=state_addr.component_id,
                lc_session_id=state_addr.session_id,
                lc_component=component_instance.get_name(),
                lc_command_name=command_name,
            )
            # Delegate fetching the state to the component instance because it may
            # want to decide not to fetch the state from Redis.
            with start_span(f"get_state({sentry_arg})"):
                state = component_instance.get_state(self, state_addr)
                if state is None:
                    raise ValueError(f"Component state not found: {state_addr}")

            command = component_instance.get_command(command_name)
            call_context: CallContext = CallContext(
                request=request,
                state=state,
                state_address=state_addr,
                state_manager=self,
            )
            with start_span(f"run_command({sentry_arg})"):
                returned_value = command(call_context, **(kwargs or {}))
            with start_span(f"process_returned_value({sentry_arg})"):
                call_context.execution_results.process_returned_value(
                    state_addr, returned_value
                )

            # Delegate saving the state to the component instance
            # because it may want to decide not to save it.
            with start_span(f"set_state({sentry_arg})"):
                component_instance.set_state(self, state_addr, state)
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
