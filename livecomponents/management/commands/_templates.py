COMPONENT_HTML_TEMPLATE = """{{% load livecomponents %}}

<div {{% component_attrs component_id %}}>
    {component_name} component
</div>
"""


COMPONENT_PYTHON_TEMPLATE = """from typing import Any
from django_components import component

from livecomponents import (
    CallContext,
    command,
    ExtraContextRequest,
    InitStateContext,
    LiveComponent,
    LiveComponentsModel,
)


class {class_name}State(LiveComponentsModel):
    \"\"\"Define the state of your component here.\"\"\"
    pass


@component.register("{component_name}")
class {class_name}Component(LiveComponent[{class_name}State]):
    template_name = "{component_name}/{proper_name}.html"


    def get_extra_context_data(
        self, extra_context_request: ExtraContextRequest[{class_name}State]
    ) -> dict[str, Any]:
        \"\"\"Return extra context to render the component template.\"\"\"
        return {{}}

    def init_state(self, context: InitStateContext) -> {class_name}State:
        return {class_name}State(**component_kwargs)

    # @command
    # def say_hello(self, call_context: CallContext[{class_name}State]):
    #     \"\"\"Example command.\"\"\"
    #     pass
"""
