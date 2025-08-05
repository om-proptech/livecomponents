from typing import Any

from django_components import component

from livecomponents import (
    CallContext,
    ExtraContextRequest,
    InitStateContext,
    LiveComponent,
    LiveComponentsModel,
    command,
)


class RootState(LiveComponentsModel):
    value: int = 0


@component.register("nestedcounter/root")
class RootComponent(LiveComponent[RootState]):
    template_name = "nestedcounter/root/root.html"

    def get_extra_context_data(
        self, extra_context_request: ExtraContextRequest[RootState]
    ) -> dict[str, Any]:
        """Return extra context to render the component template."""
        return {}

    def init_state(self, context: InitStateContext) -> RootState:
        return RootState(**context.component_kwargs)

    @command
    def increment(self, call_context: CallContext[RootState], value: int):
        """Increment the counter."""
        call_context.state.value += value
