from django_components import register

from livecomponents import (
    CallContext,
    InitStateContext,
    LiveComponent,
    command,
)
from livecomponents.component import ExtraContextRequest
from livecomponents.exceptions import CancelRendering
from livecomponents.manager.execution_results import (
    ComponentClean,
    ComponentDirty,
    TriggerEvents,
)
from livecomponents.manager.manager import UpdateStateContext
from livecomponents.utils import LiveComponentsModel


class CardState(LiveComponentsModel):
    task_id: int = 0
    title: str = ""
    done: bool = False
    column: str = "todo"


@register("taskboard/card")
class CardComponent(LiveComponent[CardState]):
    """A single task card.

    The card keeps a copy of its task in its own state, so it can re-render
    standalone after its own commands. When the board re-renders (e.g. after
    a move), the card receives fresh kwargs and syncs its copy in
    update_state().
    """

    template_name = "taskboard/card/card.html"

    def init_state(self, context: InitStateContext) -> CardState:
        kwargs = context.component_kwargs
        return CardState(
            task_id=kwargs.get("task_id", 0),
            title=kwargs.get("title", ""),
            done=bool(kwargs.get("done", False)),
            column=kwargs.get("column", "todo"),
        )

    def update_state(self, context: UpdateStateContext) -> None:
        """Sync the card's copy of the task from the kwargs.

        The kwargs are only passed when the card is rendered by its column
        (i.e. when the board re-renders). On standalone re-renders (after the
        card's own command) the kwargs are empty, and the card keeps its own
        state.
        """
        kwargs = context.component_kwargs
        if "title" in kwargs:
            context.state.title = kwargs["title"]
        if "done" in kwargs:
            context.state.done = bool(kwargs["done"])
        if "column" in kwargs:
            context.state.column = kwargs["column"]

    def get_extra_context_data(
        self, extra_context_request: ExtraContextRequest[CardState]
    ) -> dict:
        state = extra_context_request.state

        # The board is the source of truth. If the task was deleted (e.g. from
        # another tab) while this card is being re-rendered standalone, there
        # is nothing to render: cancel instead of showing a stale card.
        board_addr = extra_context_request.state_addr.must_find_ancestor(
            "taskboard/board"
        )
        board_state = extra_context_request.state_manager.get_component_state(
            board_addr
        )
        if board_state is None or all(
            task.id != state.task_id for task in board_state.tasks
        ):
            raise CancelRendering()

        # The highlight is kept on the board, so it survives board
        # re-renders without being copied into every card.
        highlighted = bool(
            board_state.highlight
            and board_state.highlight.lower() in state.title.lower()
        )
        return {"highlighted": highlighted, "columns": ["todo", "doing", "done"]}

    @command
    def toggle_done(self, call_context: CallContext[CardState]):
        call_context.state.done = not call_context.state.done
        # Keep the board (the source of truth) in sync. toggle_task() returns
        # ComponentClean(), so the board is NOT re-rendered: only this card
        # is swapped.
        call_context.find_ancestor("taskboard/board").toggle_task(
            task_id=call_context.state.task_id
        )
        # A command can return a list of execution results. Returning
        # TriggerEvents alone would NOT mark the card as dirty (the implicit
        # ComponentDirty only applies when a command returns None).
        return [
            ComponentDirty(),
            TriggerEvents.single(
                name="taskboard:toast",
                detail={
                    "message": (
                        f"Task {call_context.state.title!r} marked as "
                        f"{'done' if call_context.state.done else 'not done'}."
                    )
                },
            ),
        ]

    @command
    def move_to(self, call_context: CallContext[CardState], to_column: str):
        # The move affects two columns, so the whole board re-renders
        # (move_task defaults to ComponentDirty for the board). This card is
        # also marked dirty by default — the dirty-components deduplication
        # drops it, because the board (its ancestor) is re-rendered anyway.
        call_context.find_ancestor("taskboard/board").move_task(
            task_id=call_context.state.task_id, to_column=to_column
        )

    @command
    def remove(self, call_context: CallContext[CardState]):
        call_context.find_ancestor("taskboard/board").delete_task(
            task_id=call_context.state.task_id
        )
        return ComponentClean()
