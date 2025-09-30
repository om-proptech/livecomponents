import abc
from collections.abc import Callable
from typing import Any, Generic

from django.core.exceptions import BadRequest
from django.http import HttpRequest
from django_components import component
from django_components.component import SimplifiedInterfaceMediaDefiningClass

from livecomponents.const import DEFAULT_OWN_ID
from livecomponents.manager import StateManager, get_state_manager
from livecomponents.manager.manager import InitStateContext, UpdateStateContext
from livecomponents.sentry_utils import start_span
from livecomponents.types import State, StateAddress
from livecomponents.utils import LiveComponentsModel, find_component_id

DEFAULT_PARENT_ID = ""

COMMAND_MARKER = "__livecomponents_command__"


def command(func):
    """A decorator to mark the method as a command."""
    setattr(func, COMMAND_MARKER, True)
    return func


class LiveComponentMeta(abc.ABCMeta, SimplifiedInterfaceMediaDefiningClass):
    pass


class LiveComponent(component.Component, Generic[State], metaclass=LiveComponentMeta):
    def get_command(self, command_name: str) -> Callable:
        """Get a command method by name.

        Raise a ValueError if the command does not exist.
        """
        command_func = getattr(self, command_name, None)
        if not command_func:
            raise BadRequest(f"Command {command_name} does not exist.")
        if not getattr(command_func, COMMAND_MARKER, False):
            raise BadRequest(f"Command {command_name} does not exist.")
        return command_func

    def get_state(
        self, state_manager: StateManager, state_addr: StateAddress
    ) -> State | None:
        """Get the state of this component."""
        return state_manager.get_component_state(state_addr)

    def get_or_create_state(
        self,
        state_manager: StateManager,
        state_addr: StateAddress,
        request: HttpRequest,
        component_kwargs: dict[str, Any],
    ) -> State:
        """Internal function to get or create the state of this component.

        We used it to override the function for the stateless component
        where we don't need to store the state in Redis.
        """
        return state_manager.get_or_create_component_state(
            request,
            state_addr,
            self.init_state,
            self.update_state,
            self.outer_context,
            component_kwargs,
        )

    def get_context_data(
        self,
        own_id: str = DEFAULT_OWN_ID,
        parent_id: str = DEFAULT_PARENT_ID,
        full_component_id: str | None = None,
        **component_kwargs,
    ):
        with start_span(f"get_context_data({self.get_name()})"):
            # Fetch some data from the outer context
            session_id = self.outer_context["LIVECOMPONENTS_SESSION_ID"]
            request = self.outer_context["request"]

            component_id = find_component_id(
                full_component_id=full_component_id,
                component_name=self.registered_name,
                own_id=own_id,
                parent_id=parent_id,
            )
            state_addr = StateAddress(
                session_id=session_id,
                component_id=component_id,
            )
            state_manager = get_state_manager()
            with start_span(f"get_or_create_state({self.get_name()})"):
                state = self.get_or_create_state(
                    state_manager, state_addr, request, component_kwargs
                )
            extra_context_request: ExtraContextRequest[State] = ExtraContextRequest(
                request=request,
                state=state,
                state_manager=state_manager,
                state_addr=state_addr,
                component_kwargs=component_kwargs,
            )
            with start_span(f"get_extra_context_data({self.get_name()})"):
                extra_context = self.get_extra_context_data(extra_context_request)
            context = {
                **component_kwargs,
                **state.model_dump(),
                **extra_context,
                # Put "session_id" and "component_id" last to ensure they are
                # not overwritten
                **state_addr.model_dump(),
            }
            return context

    def get_extra_context_data(
        self, extra_context_request: "ExtraContextRequest[State]"
    ) -> dict:
        """Optionally add additional context data to the component.

        Override this method to add additional context data to the component.

        Extra context request is a dataclass that contains enough information to
        calculate the extra context data. It contains the following fields:

        - request: The current request.
        - state: The state of the component that's been previously initialized by
            `init_state`. The state is stored in Redis and is maintained between
            re-renders of the component.
        - state_manager: The state manager. You can use the manager to get the state
            of other components.
        - state_addr: The state address of the component. You can use
            state_addr.with_component_id() to get the state address of other
            components.
        - component_kwargs: The keyword arguments passed to the component in the
            template tag. For example, if the component is rendered with
            `{% component "mycomponent" foo="bar" %}`, then `component_kwargs`
            will be `{"foo": "bar"}`. Remember that when the component is
            re-rendered as a result of the command execution, no component
            kwargs are passed.
        """
        return {}

    @abc.abstractmethod
    def init_state(self, context: InitStateContext) -> State:
        ...

    def update_state(self, context: UpdateStateContext) -> None:
        """Update in-place the state of this component if necessary during a re-render.

        This method is invoked in two scenarios:

        1. When the parent component re-renders and subsequently renders this child
           component, often due to the parent's command execution.
        2. When this child component re-renders independently, typically triggered by
           its own command execution.

        The **kwargs parameter contains arguments passed to this live component in the
        template. For example, {% livecomponent "dialog" title="Foo" %} results in
        kwargs as {"title": "Foo"}.

        Note: If the component re-renders by itself, **kwargs will not be passed,
        resulting in empty string values in kwargs.

        This method is primarily useful when the parent component re-renders and
        chooses to update the state of its child components. The child component should
        process **kwargs to determine if a state update is necessary.

        Example:
            def update_state(self, context: UpdateStateContext, **kwargs) -> State:
                if kwargs.get("title"):
                    context.state.title = kwargs["title"]
        """
        pass

    def render(self, context):
        with start_span(f"render({self.get_name()})"):
            return super().render(context)

    def get_name(self):
        return self.__class__.__name__


class StatelessModel(LiveComponentsModel):
    pass


class StatelessLiveComponent(LiveComponent[StatelessModel]):
    """A stateless subclass of LiveComponent.

    Technically, it still stores the state in Redis, but the state is always
    initialized to an empty model.

    Usually, the state is stored outside the component, e.g. in the parent
    component, and can be addressed from get_extra_context_data() where
    extra_context_request contains the state_manager and state_addr.
    """

    def get_state(
        self, state_manager: StateManager, state_addr: StateAddress
    ) -> StatelessModel | None:
        return StatelessModel()

    def get_or_create_state(
        self,
        state_manager: StateManager,
        state_addr: StateAddress,
        request: HttpRequest,
        component_kwargs: dict[str, Any],
    ) -> StatelessModel:
        return StatelessModel()

    def init_state(self, context: InitStateContext) -> StatelessModel:
        return StatelessModel()


class ExtraContextRequest(LiveComponentsModel, Generic[State]):
    request: HttpRequest
    state: State
    state_manager: StateManager
    state_addr: StateAddress
    component_kwargs: dict[str, Any]
