import pytest

from livecomponents.types import ComponentId, StateAddress


def test_state_address_find_ancestor_returns_ancestor():
    state_address = StateAddress(
        session_id="session_id", component_id="|root:0|a:1|b:2|c:3"
    )
    ancestor = state_address.find_ancestor("a")
    assert ancestor == StateAddress(session_id="session_id", component_id="|root:0|a:1")


def test_state_address_find_ancestor_returns_none():
    state_address = StateAddress(
        session_id="session_id", component_id="|root:0|a:1|b:2|c:3"
    )
    ancestor = state_address.find_ancestor("d")
    assert ancestor is None


def test_state_address_must_find_ancestor_raises_value_error():
    state_address = StateAddress(
        session_id="session_id", component_id="|root:0|a:1|b:2|c:3"
    )
    with pytest.raises(ValueError):
        state_address.must_find_ancestor("d")


def test_component_id_concatenation():
    assert ComponentId("|a:0") | "b" == ComponentId("|a:0|b:0")


def test_component_id_concatenation_with_own_id():
    assert ComponentId("|a:0") | ("b", "1") == ComponentId("|a:0|b:1")


def test_state_address_concatentation():
    state_address = StateAddress(session_id="session_id", component_id="|root:0")
    assert state_address | "a" == StateAddress(
        session_id="session_id", component_id="|root:0|a:0"
    )


def test_state_address_get_parent():
    state_address = StateAddress(
        session_id="session_id", component_id="|root:0|a:1|b:2|c:3"
    )
    assert state_address.get_parent() == StateAddress(
        session_id="session_id", component_id="|root:0|a:1|b:2"
    )
