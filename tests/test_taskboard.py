"""Tests for the task board example.

The board is the most feature-dense example: these tests drive it through the
real HTTP command endpoint and assert the interactions between features
(update_state, dirty-components deduplication, ComponentClean,
CancelRendering, TriggerEvents, RefreshPage).
"""
import json
import re
from urllib.parse import urlencode

import pytest
from django.urls import reverse

from livecomponents.const import HIER_SEP, TYPE_SEP
from livecomponents.types import StateAddress

BOARD_ID = f"{HIER_SEP}taskboard/board{TYPE_SEP}main"


def card_id(column: str, task_id: int) -> str:
    return (
        f"{BOARD_ID}"
        f"{HIER_SEP}taskboard/column{TYPE_SEP}{column}"
        f"{HIER_SEP}taskboard/card{TYPE_SEP}{task_id}"
    )


@pytest.fixture
def board_page(client, state_manager):
    """Render the task board page and return (session_id, html)."""
    response = client.get(reverse("taskboard"))
    assert response.status_code == 200
    html = response.content.decode()
    match = re.search(r"session_id=([\w-]+)", html)
    assert match, "Session ID not found on the rendered page"
    return match.group(1), html


def call_command(
    client, session_id: str, component_id: str, command_name: str, **kwargs
):
    url = reverse("livecomponents:call-command")
    query = urlencode(
        {
            "session_id": session_id,
            "component_id": component_id,
            "command_name": command_name,
        }
    )
    return client.post(
        f"{url}?{query}",
        data=json.dumps(kwargs),
        content_type="application/json",
    )


def get_board_state(state_manager, session_id: str):
    return state_manager.get_component_state(
        StateAddress(session_id=session_id, component_id=BOARD_ID)
    )


def test_board_initial_render(board_page):
    session_id, html = board_page
    # Three columns with the default tasks.
    assert html.count('data-testid="taskboard-card"') == 4
    assert "Roast the beans" in html
    # The footer fill: save_context variable and the nested message block.
    assert '<span data-testid="taskboard-owner">Coffee Team</span>' in html
    assert 'data-testid="message-content"' in html


def test_move_task_rerenders_board_once(client, state_manager, board_page):
    """Moving a card re-renders the whole board exactly once.

    The card marks itself dirty (default) and the chained board command marks
    the board dirty; the dirty-components deduplication drops the card
    because its ancestor is re-rendered anyway.
    """
    session_id, _ = board_page
    response = call_command(
        client,
        session_id,
        card_id("todo", 1),
        "move_to",
        to_column="doing",
    )
    assert response.status_code == 200
    html = response.content.decode()

    # The board is re-rendered once, and the cards appear only inside it
    # (4 tasks; no extra standalone card render).
    assert html.count(f'data-livecomponent-id="{BOARD_ID}"') == 1
    assert html.count('data-testid="taskboard-card"') == 4

    # The task actually moved (board state is the source of truth)...
    board_state = get_board_state(state_manager, session_id)
    assert [task.column for task in board_state.tasks if task.id == 1] == ["doing"]

    # ...and the card's own state was synced via update_state() when the
    # column re-rendered it with fresh kwargs. Note that the card now lives
    # under the "doing" column.
    card_state = state_manager.get_component_state(
        StateAddress(session_id=session_id, component_id=card_id("doing", 1))
    )
    assert card_state.column == "doing"

    # The independent message component (updated via find_one) is
    # re-rendered too. (The quotes around task and column names are
    # HTML-escaped, so only assert on the unquoted part.)
    assert html.count('data-livecomponent-id="|message:board"') >= 1
    assert "moved to" in html


def test_toggle_done_swaps_only_the_card(client, state_manager, board_page):
    """toggle_done re-renders the card only: the board is updated silently
    (ComponentClean), and a browser event is triggered (TriggerEvents)."""
    session_id, _ = board_page
    response = call_command(client, session_id, card_id("todo", 1), "toggle_done")
    assert response.status_code == 200
    html = response.content.decode()

    # Only the card is swapped; the board is not re-rendered.
    assert html.count('data-testid="taskboard-card"') == 1
    assert f'data-livecomponent-id="{BOARD_ID}"' not in html

    # The TriggerEvents header carries the toast event.
    events = json.loads(response.headers["HX-Trigger"])
    assert "marked as done" in events["taskboard:toast"]["message"]

    # Both copies of the state are in sync.
    board_state = get_board_state(state_manager, session_id)
    assert [task.done for task in board_state.tasks if task.id == 1] == [True]


def test_rerender_of_deleted_card_is_cancelled(client, state_manager, board_page):
    """A card whose task no longer exists cancels its own re-render
    (CancelRendering) instead of rendering stale data or crashing."""
    session_id, _ = board_page
    assert (
        call_command(client, session_id, BOARD_ID, "delete_task", task_id=1).status_code
        == 200
    )

    # The card state is still in the store; its re-render gets cancelled.
    response = call_command(client, session_id, card_id("todo", 1), "toggle_done")
    assert response.status_code == 200
    html = response.content.decode()
    assert 'data-testid="taskboard-card"' not in html


def test_add_task_with_empty_title_is_clean(client, board_page):
    """add_task with a blank title returns ComponentClean: no re-render."""
    session_id, _ = board_page
    response = call_command(client, session_id, BOARD_ID, "add_task", title="  ")
    assert response.status_code == 200
    assert response.content.strip() == b""


def test_reset_board_triggers_full_page_refresh(client, state_manager, board_page):
    """reset_board returns RefreshPage: HX-Refresh header, empty body."""
    session_id, _ = board_page
    assert (
        call_command(
            client, session_id, BOARD_ID, "add_task", title="Extra task"
        ).status_code
        == 200
    )
    assert len(get_board_state(state_manager, session_id).tasks) == 5

    response = call_command(client, session_id, BOARD_ID, "reset_board")
    assert response.status_code == 200
    assert response.headers["HX-Refresh"] == "true"
    assert response.content.strip() == b""
    assert len(get_board_state(state_manager, session_id).tasks) == 4


def test_highlight_marks_matching_cards(client, board_page):
    """set_highlight re-renders the board; matching cards get highlighted
    (the highlight lives on the board and is read by the cards)."""
    session_id, _ = board_page
    response = call_command(
        client, session_id, BOARD_ID, "set_highlight", highlight="brew"
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert html.count('data-highlighted="true"') == 1
    assert "Brew the coffee" in html
