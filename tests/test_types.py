import pytest

from livecomponents.types import StateAddress


def test_state_address_find_ancestor_returns_ancestor():
    state_address = StateAddress(
        session_id="session_id", component_id="root:0|a:1|b:2|c:3"
    )
    ancestor = state_address.find_ancestor("a")
    assert ancestor == StateAddress(session_id="session_id", component_id="root:0|a:1")


def test_state_address_find_ancestor_returns_none():
    state_address = StateAddress(
        session_id="session_id", component_id="root:0|a:1|b:2|c:3"
    )
    ancestor = state_address.find_ancestor("d")
    assert ancestor is None


def test_state_address_must_find_ancestor_raises_value_error():
    state_address = StateAddress(
        session_id="session_id", component_id="root:0|a:1|b:2|c:3"
    )
    with pytest.raises(ValueError):
        state_address.must_find_ancestor("d")
