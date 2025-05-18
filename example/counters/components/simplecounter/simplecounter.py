from django_components import component

from livecomponents import (
    LiveComponent,
    LiveComponentsModel,
    command,
)


class SimplecounterState(LiveComponentsModel):
    count: int = 0


@component.register("simplecounter")
class SimplecounterComponent(LiveComponent[SimplecounterState]):
    template_name = "simplecounter/simplecounter.html"

    def init_state(self, context):
        return SimplecounterState()

    @command
    def increment(self, call_context):
        """Example command."""
        call_context.state.count += 1

    @command
    def decrement(self, call_context):
        """Example command."""
        call_context.state.count -= 1
