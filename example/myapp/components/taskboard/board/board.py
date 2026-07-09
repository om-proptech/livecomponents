from django_components import register

from livecomponents import (
    CallContext,
    InitStateContext,
    LiveComponent,
    command,
)
from livecomponents.const import HIER_SEP, TYPE_SEP
from livecomponents.manager.execution_results import ComponentClean, RefreshPage
from livecomponents.utils import LiveComponentsModel

COLUMNS = ["todo", "doing", "done"]

DEFAULT_TASKS = [
    ("Roast the beans", "todo"),
    ("Grind the beans", "todo"),
    ("Brew the coffee", "doing"),
    ("Buy green beans", "done"),
]


class Task(LiveComponentsModel):
    id: int
    title: str
    column: str = "todo"
    done: bool = False


class BoardState(LiveComponentsModel):
    tasks: list[Task] = []
    highlight: str = ""
    next_id: int = 1


def default_board_state() -> BoardState:
    state = BoardState()
    for title, column in DEFAULT_TASKS:
        state.tasks.append(
            Task(id=state.next_id, title=title, column=column, done=column == "done")
        )
        state.next_id += 1
    return state


@register("taskboard/board")
class BoardComponent(LiveComponent[BoardState]):
    """The root component of the task board.

    The board owns the list of tasks (the single source of truth). Columns
    are stateless and read the board state; cards keep a copy of their task
    in their own state, refreshed via update_state() whenever the board
    re-renders them with new kwargs.
    """

    template_name = "taskboard/board/board.html"

    def init_state(self, context: InitStateContext) -> BoardState:
        return default_board_state()

    def find_task(self, state: BoardState, task_id: int) -> Task | None:
        for task in state.tasks:
            if task.id == task_id:
                return task
        return None

    @command
    def add_task(self, call_context: CallContext[BoardState], title: str):
        title = title.strip()
        if not title:
            # Nothing to add; skip the re-render altogether.
            return ComponentClean()
        state = call_context.state
        state.tasks.append(Task(id=state.next_id, title=title))
        state.next_id += 1
        return None  # Defaults to ComponentDirty().

    @command
    def toggle_task(self, call_context: CallContext[BoardState], task_id: int):
        """Toggle a task, without re-rendering the board.

        Called by the card component, which re-renders itself: the board
        state is updated silently (ComponentClean), so only the card is
        swapped in the response.
        """
        task = self.find_task(call_context.state, task_id)
        if task is not None:
            task.done = not task.done
        return ComponentClean()

    @command
    def move_task(
        self, call_context: CallContext[BoardState], task_id: int, to_column: str
    ):
        if to_column not in COLUMNS:
            return ComponentClean()
        task = self.find_task(call_context.state, task_id)
        if task is not None:
            task.column = to_column
            # Update the (independent) message component rendered in the
            # board's footer fill. Executing its command marks it as dirty,
            # so it is re-rendered along with the board.
            call_context.find_one(f"{HIER_SEP}message{TYPE_SEP}board").set_message(
                message=f"Task {task.title!r} moved to {to_column!r}."
            )
        return None  # The whole board re-renders.

    @command
    def delete_task(self, call_context: CallContext[BoardState], task_id: int):
        call_context.state.tasks = [
            task for task in call_context.state.tasks if task.id != task_id
        ]
        return None  # The whole board re-renders.

    @command
    def set_highlight(self, call_context: CallContext[BoardState], highlight: str):
        call_context.state.highlight = highlight
        return None  # Re-render: cards receive the new highlight kwarg.

    @command
    def reset_board(self, call_context: CallContext[BoardState]):
        new_state = default_board_state()
        call_context.state.tasks = new_state.tasks
        call_context.state.next_id = new_state.next_id
        call_context.state.highlight = ""
        return RefreshPage()
