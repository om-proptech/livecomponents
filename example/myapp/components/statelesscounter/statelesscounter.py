from django_components import component

from livecomponents import CallContext, StatelessLiveComponent, command
from livecomponents.component import ExtraContextRequest, StatelessModel
from livecomponents.manager.execution_results import ComponentDirty

# A global variable simulating external storage (database, file, Redis, etc.).
# The point: the component is "stateless" from livecomponents' perspective,
# but it still has state — just managed elsewhere.
_counter_value = 0


@component.register("statelesscounter")
class StatelessCounterComponent(StatelessLiveComponent):
    """A counter that stores its value outside of livecomponents.

    Demonstrates that StatelessLiveComponent can have commands and manage
    state externally (e.g. in a database, a file, or — as here — a global
    variable).
    """

    template_name = "statelesscounter/statelesscounter.html"

    def get_extra_context_data(
        self, extra_context_request: ExtraContextRequest[StatelessModel]
    ) -> dict:
        return {"count": _counter_value}

    @command
    def increment(self, call_context: CallContext):
        global _counter_value
        _counter_value += 1
        return ComponentDirty()

    @command
    def decrement(self, call_context: CallContext):
        global _counter_value
        _counter_value -= 1
        return ComponentDirty()

