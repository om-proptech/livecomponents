COMPONENT_HTML_TEMPLATE = """
{{% load livecomponents %}}

<div {{% component_attrs component_id %}}>
    {component_name} component
</div>
"""


COMPONENT_PYTHON_TEMPLATE = """
from typing import Any
from django_components import component
from pydantic import BaseModel

from livecomponents import CallContext, InitStateContext, LiveComponent, command


class {component_name}State(BaseModel):
    pass


@component.register("{lowercase_component_name}")
class {component_name}(LiveComponent[{component_name}State]):
    template_name = "{lowercase_component_name}/{lowercase_component_name}.html"

    def get_extra_context_data(self, state: {component_name}State) -> dict[str, Any]:
        return {{}}

    def init_state(
        self, context: InitStateContext, **component_kwargs
    ) -> {component_name}State:
        return {component_name}State(**component_kwargs)

    # @command
    # def say_hello(self, call_context: CallContext[{component_name}State]):
    #     \"\"\"Example command.\"\"\"
    #     pass
"""
