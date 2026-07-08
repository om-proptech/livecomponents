from django_components import register

from livecomponents import StatelessLiveComponent
from livecomponents.component import ExtraContextRequest, StatelessModel


@register("taskboard/column")
class ColumnComponent(StatelessLiveComponent):
    """A stateless column that reads the task list from the board's state.

    Demonstrates how a stateless component addresses an ancestor's state via
    the state manager, and how it stays correct when rendered with an
    isolated context (the board renders columns with the `only` flag).
    """

    template_name = "taskboard/column/column.html"

    def get_extra_context_data(
        self, extra_context_request: ExtraContextRequest[StatelessModel]
    ) -> dict:
        kwargs = extra_context_request.component_kwargs
        column = kwargs.get("column", "")

        board_addr = extra_context_request.state_addr.must_find_ancestor(
            "taskboard/board"
        )
        board_state = extra_context_request.state_manager.get_component_state(
            board_addr
        )
        if board_state is None:
            return {"tasks": []}
        tasks = [task for task in board_state.tasks if task.column == column]
        return {"tasks": tasks}
