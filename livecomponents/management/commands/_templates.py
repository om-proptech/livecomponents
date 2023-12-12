COMPONENT_HTML_TEMPLATE = """{{% load livecomponents %}}

<div {{% component_attrs component_id %}}>
    {component_name} component
</div>
"""


COMPONENT_PYTHON_TEMPLATE = """from typing import Any
from django_components import component

from livecomponents import CallContext, InitStateContext, LiveComponent, command
from livecomponents.utils import LiveComponentsModel


class {class_name}State(LiveComponentsModel):
    \"\"\"Define the state of your component here.\"\"\"
    pass


@component.register("{component_name}")
class {class_name}Component(LiveComponent[{class_name}State]):
    template_name = "{component_name}/{proper_name}.html"

    def get_extra_context_data(
        self, state: {class_name}State, **component_kwargs
    ) -> dict[str, Any]:
        \"\"\"Return extra context to render the component template.

        Args:
            state: The state of the component, that's been previously initialized
                by `init_state`. The state is stored in Redis and is maintained
                between re-renders of the component.
            component_kwargs: The keyword arguments passed to the component in the
                template tag. For example, if the component is rendered with
                `{% component "mycomponent" foo="bar" %}`, then `component_kwargs`
                will be `{"foo": "bar"}`. Remember that when the component is
                re-rendered as a result of the command execution, no component
                kwargs are passed.

        Returns:
            A dictionary with extra context to render the component template.
        \"\"\"
        return {{}}

    def init_state(
        self, context: InitStateContext, **component_kwargs
    ) -> {class_name}State:
        return {class_name}State(**component_kwargs)

    # @command
    # def say_hello(self, call_context: CallContext[{class_name}State]):
    #     \"\"\"Example command.\"\"\"
    #     pass
"""
