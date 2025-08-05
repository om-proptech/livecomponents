from django_components import component
from pydantic import BaseModel

from livecomponents import InitStateContext, LiveComponent


class SampleState(BaseModel):
    message: str = "message"
    var: str = "unset"


@component.register("sample")
class SampleComponent(LiveComponent[SampleState]):
    template_name = "sample/sample.html"

    def init_state(self, context: InitStateContext) -> SampleState:
        var = context.outer_context.get("var", "unset")
        effective_kwargs = {**context.component_kwargs, "var": var}
        return SampleState(**effective_kwargs)
