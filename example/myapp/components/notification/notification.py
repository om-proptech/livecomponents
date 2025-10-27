from django_components import component

from livecomponents import (
    CallContext,
    InitStateContext,
    LiveComponent,
    LiveComponentsModel,
    command,
)
from livecomponents.manager.execution_results import (
    ComponentDirty,
    Event,
    Trigger,
    TriggerEvents,
)


class NotificationState(LiveComponentsModel):
    """State for the notification demo component."""

    click_count: int = 0
    last_message: str = ""


@component.register("notification")
class NotificationComponent(LiveComponent[NotificationState]):
    """Demo component showing how to trigger custom browser events."""

    template_name = "notification/notification.html"

    def init_state(self, context: InitStateContext) -> NotificationState:
        return NotificationState()

    @command
    def trigger_success(self, call_context: CallContext[NotificationState]) -> list:
        """Trigger a success notification event."""
        call_context.state.click_count += 1
        call_context.state.last_message = "Success notification triggered!"

        return [
            ComponentDirty(),
            TriggerEvents.single(
                name="showNotification",
                detail={
                    "message": "Operation completed successfully!",
                    "level": "success",
                },
            ),
        ]

    @command
    def trigger_info(self, call_context: CallContext[NotificationState]) -> list:
        """Trigger an info notification event."""
        call_context.state.click_count += 1
        call_context.state.last_message = "Info notification triggered!"

        return [
            ComponentDirty(),
            TriggerEvents.single(
                name="showNotification",
                detail={
                    "message": "Here is some information for you.",
                    "level": "info",
                },
            ),
        ]

    @command
    def trigger_multiple(self, call_context: CallContext[NotificationState]) -> list:
        """Trigger multiple events at once."""
        call_context.state.click_count += 1
        call_context.state.last_message = "Multiple events triggered!"

        return [
            ComponentDirty(),
            TriggerEvents(
                [
                    Event(
                        name="showNotification",
                        detail={
                            "message": (
                                "Multiple events triggered "
                                "(check out the developer console)!"
                            ),
                            "level": "success",
                        },
                    ),
                    Event(name="logAnalytics", detail={"action": "trigger_multiple"}),
                ]
            ),
        ]

    @command
    def trigger_after_settle(
        self, call_context: CallContext[NotificationState]
    ) -> list:
        """Trigger event after DOM settles."""
        call_context.state.click_count += 1
        call_context.state.last_message = "After-settle event triggered!"

        return [
            ComponentDirty(),
            TriggerEvents.single(
                name="showNotification",
                detail={
                    "message": "This event fired after DOM settled.",
                    "level": "info",
                },
                trigger=Trigger.AFTER_SETTLE,
            ),
        ]
