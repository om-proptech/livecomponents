from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import InitStateContext


class SampleState(BaseModel):
    message: str = "message"
    var: str = "unset"


@component.register("sample")
class SampleComponent(LiveComponent[SampleState]):
    template_name = "sample/sample.html"

    @classmethod
    def init_state(cls, context: InitStateContext, **component_kwargs) -> SampleState:
        var = context.outer_context.get("var", "unset")
        effective_kwargs = {**component_kwargs, "var": var}
        return SampleState(**effective_kwargs)
