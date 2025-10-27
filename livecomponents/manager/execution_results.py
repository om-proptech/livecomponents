import abc
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from livecomponents.types import StateAddress


class IExecutionResult(abc.ABC):
    """Abstract base class t modify component state or behavior."""

    @abc.abstractmethod
    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        """Process this execution result."""
        ...


class ComponentDirty(IExecutionResult):
    """Mark a component as dirty to trigger re-rendering.

    This is the default behavior when a command handler returns None.

    **Example:**

    ```python
    class StockComponent(LiveComponent):
        ...

        @command
        def update_stock(self, call_context: CallContext[StockState]):
            \"\"\"Update stock quantity. Component automatically re-renders\"\"\"
            call_context.state.bean.stock_quantity += 1
            call_context.state.bean.save()
            # Returns ComponentDirty() by default
    ```
    """

    def __init__(self, component_id: str | None = None):
        """Mark the component as dirty.

        If component_id is None, the current component is marked as dirty. Otherwise,
        use the component_id to mark another component as dirty.
        """
        self.component_id = component_id

    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        """Add the component to the dirty components set."""
        if self.component_id is not None:
            state_address = state_address.with_component_id(self.component_id)
        results.dirty_components.add(state_address)


class ParentDirty(IExecutionResult):
    """Mark the parent component as dirty to trigger re-rendering.

    Useful when a child component performs an action that affects the parent's data,
    such as deleting an item from a list or updating shared state.

    **Example:**

    ```python
    class CartComponent(LiveComponent):
        ...

        @command
        def add_to_cart(self, call_context: CallContext[CartState], product_id: int):
            \"\"\"Add item to cart and update parent cart counter\"\"\"
            self.state.cart.append(product_id)
            return ParentDirty()
    ```
    """

    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        """Add the parent component to the dirty components set."""
        results.dirty_components.add(state_address.must_get_parent())


class ComponentClean(IExecutionResult):
    """Indicate that a component is clean and requires no re-rendering.

    Use this when a command performs side effects (like logging, analytics, or
    background tasks) that don't change the component's visual state.

    **Example:**

    ```python
    class AnalyticsComponent(LiveComponent):
        ...

        @command
        def track_click(self, call_context: CallContext[AnalyticsState], event_name: str):
            \"\"\"Log user action without re-rendering the component\"\"\"
            self.analytics.track(event_name, call_context.state.user_id)
            return ComponentClean()
    ```
    """  # noqa: E501

    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        """No-op processing for clean components."""
        pass


class RefreshPage(IExecutionResult):
    """Trigger a full page refresh in the browser.

    Sets the HX-Refresh header to instruct HTMX to reload the entire page.
    Use sparingly, as it breaks the SPA-like experience.

    **Example:**

    ```python
    class SettingsComponent(LiveComponent):
        ...

        @command
        def switch_language(self, call_context: CallContext[SettingsState], language: str):
            \"\"\"Switch language and refresh page to apply changes\"\"\"
            call_context.request.session['language'] = language
            return RefreshPage()
    ```
    """  # noqa: E501

    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        """Set the HX-Refresh header to trigger page refresh."""
        results.response_headers["HX-Refresh"] = "true"


class RedirectPage(IExecutionResult):
    """Redirect the browser to a different URL.

    Sets the HX-Redirect header to instruct HTMX to navigate to a new page.
    Commonly used after successful form submissions or authentication.

    **Example:**

    ```python
    class LoginComponent(LiveComponent):
        ...

        @command
        def login(self, call_context: CallContext[LoginState], username: str, password: str):
            \"\"\"Authenticate user and redirect to dashboard\"\"\"
            user = authenticate(username=username, password=password)
            if user:
                login(call_context.request, user)
                return RedirectPage('/dashboard/')
            call_context.state.error = 'Invalid credentials'
    ```
    """  # noqa: E501

    def __init__(self, url: str):
        """Initialize with the target URL for redirection."""
        self.url = url

    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        """Set the HX-Redirect header to trigger page redirection."""
        results.response_headers["HX-Redirect"] = self.url


class ReplaceUrl(IExecutionResult):
    """Replace the current URL in the browser without reloading the page.

    Updates the browser's address bar and history without triggering a full page reload.
    Useful for maintaining clean URLs that reflect the current application state.
    See https://htmx.org/headers/hx-replace-url/.

    **Example:**

    ```python
    class ProductListComponent(LiveComponent):
        ...

        @command
        def apply_search_filter(self, call_context: CallContext[ProductListState], search_term: str):
            \"\"\"Apply search filter and update URL to reflect current state\"\"\"
            call_context.state.search = search_term
            if search_term:
                return ReplaceUrl(f'/products/?search={search_term}')
            else:
                return ReplaceUrl('/products/')
    ```
    """  # noqa: E501

    def __init__(self, url: str):
        """Initialize with the URL to replace in the browser."""
        self.url = url

    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        """Set the HX-Replace-Url header to update the browser URL."""
        results.response_headers["HX-Replace-Url"] = self.url


class PushUrl(IExecutionResult):
    """Push a new URL to the browser history without reloading the page.

    Updates the browser's address bar and adds a new entry to the browser history,
    allowing users to navigate back to previous states using the browser's back button.
    See https://htmx.org/headers/hx-push-url/.

    **Example:**

    ```python
    class WizardComponent(LiveComponent):
        ...

        @command
        def next_step(self, call_context: CallContext[WizardState]):
            \"\"\"Move to next step and update URL with history entry\"\"\"
            call_context.state.current_step += 1
            return PushUrl(f'/wizard/step-{call_context.state.current_step}/')
    ```
    """  # noqa: E501

    def __init__(self, url: str):
        """Initialize with the URL to push to the browser history."""
        self.url = url

    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        """Set the HX-Push-Url header to push a new URL to browser history."""
        results.response_headers["HX-Push-Url"] = self.url


class Trigger(Enum):
    """Specifies when events should be triggered in the HTMX lifecycle.

    See https://htmx.org/headers/hx-trigger/
    """

    AFTER_REQUEST = "HX-Trigger"
    AFTER_SETTLE = "HX-Trigger-After-Settle"
    AFTER_SWAP = "HX-Trigger-After-Swap"


class Event(BaseModel):
    """Represents a browser event to be triggered via HX-Trigger headers.

    Attributes:
        name: The name of the event to trigger in the browser.
        target: Optional CSS selector for the element to trigger the event on.
                If None, the event is triggered on the element that
                initiated the request.
        detail: Dictionary of additional data to pass with the event. This data
                will be available in the event's detail property in JavaScript
                event listeners.
    """

    name: str
    target: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)

    def serialize_value(self) -> dict[str, Any]:
        ret = self.detail.copy()
        if self.target is not None:
            ret["target"] = self.target
        return ret


class TriggerEvents(IExecutionResult):
    """Trigger custom browser events via HTMX response headers.

    Allows you to trigger JavaScript events in the browser that can be listened to
    with standard event listeners. Useful for coordinating between components,
    showing notifications, or triggering client-side actions after server processing.

    See https://htmx.org/headers/hx-trigger/ for more details.

    **Example:**

    ```python
    class NotificationComponent(LiveComponent):
        ...

        @command
        def save_data(self, call_context: CallContext[NotificationState]):
            \"\"\"Save data and show success notification\"\"\"
            call_context.state.data.save()
            return TriggerEvents([
                Event(
                    name="showNotification",
                    detail={"message": "Data saved successfully!", "level": "success"}
                )
            ])

        @command
        def refresh_dashboard(self, call_context: CallContext[NotificationState]):
            \"\"\"Trigger multiple events after data update\"\"\"
            call_context.state.update_data()
            return TriggerEvents([
                Event(name="refreshChart", detail={"chartId": "sales-chart"}),
                Event(name="updateCounter", target="#cart-counter"),
            ])
    ```

    **Using the convenience method for single events:**

    ```python
    @command
    def quick_action(self, call_context: CallContext[State]):
        return TriggerEvents.single(
            name="actionComplete",
            detail={"timestamp": time.time()}
        )
    ```
    """

    def __init__(self, events: list[Event], trigger: Trigger = Trigger.AFTER_REQUEST):
        """Initialize with the list of events to trigger.

        Args:
            events: List of Event objects to trigger. Event names must be unique.
            trigger: When to trigger the events (default: immediately after response).

        Raises:
            ValueError: If duplicate event names are found.
        """
        # Validate no duplicate event names
        event_names = [event.name for event in events]
        if len(event_names) != len(set(event_names)):
            duplicates = [name for name in event_names if event_names.count(name) > 1]
            raise ValueError(
                f"Duplicate event names found: {', '.join(set(duplicates))}. "
                "Each event name must be unique."
            )

        self.events = events
        self.trigger = trigger

    @classmethod
    def single(
        cls,
        name: str,
        detail: dict[str, Any] | None = None,
        target: str | None = None,
        trigger: Trigger = Trigger.AFTER_REQUEST,
    ) -> "TriggerEvents":
        """Create a TriggerEvents instance with a single event.

        Convenience method for the common case of triggering just one event.

        Args:
            name: The name of the event to trigger.
            detail: Optional dictionary of data to pass with the event.
            target: Optional CSS selector for the target element.
            trigger: When to trigger the event (default: immediately after response).

        Returns:
            A TriggerEvents instance with a single event.
        """
        return cls(
            [Event(name=name, detail=detail or {}, target=target)],
            trigger=trigger,
        )

    def process(self, state_address: StateAddress, results: "ExecutionResults") -> None:
        """Set the HX-Trigger header to trigger the events."""
        results.response_headers[self.trigger.value] = json.dumps(
            self.serialize_events()
        )

    def serialize_events(self) -> dict[str, Any]:
        """Serialize the events to a dictionary."""
        return {event.name: event.serialize_value() for event in self.events}


class ExecutionResults(BaseModel):
    """Container for execution results."""

    dirty_components: set[StateAddress] = Field(default_factory=set)
    response_headers: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)

    def is_partial_render_necessary(self) -> bool:
        """Check if partial rendering is needed based on response headers."""
        full_rerender_headers = ["HX-Redirect", "HX-Refresh"]
        for header in self.response_headers:
            if header in full_rerender_headers:
                return False
        return True

    def process_returned_value(
        self,
        state_address: StateAddress,
        value: list[IExecutionResult] | IExecutionResult | None,
    ) -> None:
        """Process the command handler's returned value.

        If value is None, defaults to ComponentDirty() to mark the component as dirty.
        """
        if value is None:
            value = [ComponentDirty()]
        if not isinstance(value, list):
            value = [value]
        for command in value:
            if not isinstance(command, IExecutionResult):
                raise RuntimeError(
                    "The function returned an invalid value. "
                    "Expected None or a subclass of IComponentCommand."
                )
            command.process(state_address, self)
