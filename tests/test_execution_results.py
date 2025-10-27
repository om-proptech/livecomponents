import json

import pytest

from livecomponents.manager.execution_results import (
    Event,
    ExecutionResults,
    Trigger,
    TriggerEvents,
)
from livecomponents.types import ComponentId, StateAddress


@pytest.fixture
def state_address():
    """Create a basic state address for testing."""
    return StateAddress(
        session_id="test-session",
        component_id=ComponentId("test-component"),
    )


@pytest.fixture
def execution_results():
    """Create a basic execution results container for testing."""
    return ExecutionResults()


def test_event_serialization_with_detail():
    """Test Event serialization with detail data."""
    event = Event(
        name="showNotification",
        detail={"message": "Hello", "level": "success"},
    )
    serialized = event.serialize_value()
    assert serialized == {"message": "Hello", "level": "success"}


def test_event_serialization_with_target():
    """Test Event serialization with target selector."""
    event = Event(
        name="updateCounter",
        target="#cart-counter",
        detail={"count": 5},
    )
    serialized = event.serialize_value()
    assert serialized == {"count": 5, "target": "#cart-counter"}


def test_event_serialization_empty():
    """Test Event serialization with no detail or target."""
    event = Event(name="simpleEvent")
    serialized = event.serialize_value()
    assert serialized == {}


def test_trigger_events_single_event(state_address, execution_results):
    """Test TriggerEvents with a single event."""
    trigger = TriggerEvents([Event(name="myEvent", detail={"foo": "bar"})])
    trigger.process(state_address, execution_results)

    assert "HX-Trigger" in execution_results.response_headers
    header_value = json.loads(execution_results.response_headers["HX-Trigger"])
    assert header_value == {"myEvent": {"foo": "bar"}}


def test_trigger_events_multiple_events(state_address, execution_results):
    """Test TriggerEvents with multiple events."""
    trigger = TriggerEvents(
        [
            Event(name="event1", detail={"data": "value1"}),
            Event(name="event2", detail={"data": "value2"}),
        ]
    )
    trigger.process(state_address, execution_results)

    assert "HX-Trigger" in execution_results.response_headers
    header_value = json.loads(execution_results.response_headers["HX-Trigger"])
    assert header_value == {
        "event1": {"data": "value1"},
        "event2": {"data": "value2"},
    }


def test_trigger_events_after_settle(state_address, execution_results):
    """Test TriggerEvents with AFTER_SETTLE trigger."""
    trigger = TriggerEvents(
        [Event(name="myEvent")],
        trigger=Trigger.AFTER_SETTLE,
    )
    trigger.process(state_address, execution_results)

    assert "HX-Trigger-After-Settle" in execution_results.response_headers
    header_value = json.loads(
        execution_results.response_headers["HX-Trigger-After-Settle"]
    )
    assert header_value == {"myEvent": {}}


def test_trigger_events_after_swap(state_address, execution_results):
    """Test TriggerEvents with AFTER_SWAP trigger."""
    trigger = TriggerEvents(
        [Event(name="myEvent")],
        trigger=Trigger.AFTER_SWAP,
    )
    trigger.process(state_address, execution_results)

    assert "HX-Trigger-After-Swap" in execution_results.response_headers
    header_value = json.loads(
        execution_results.response_headers["HX-Trigger-After-Swap"]
    )
    assert header_value == {"myEvent": {}}


def test_trigger_events_duplicate_names_raises_error():
    """Test that duplicate event names raise ValueError."""
    with pytest.raises(ValueError, match="Duplicate event names found: event1"):
        TriggerEvents(
            [
                Event(name="event1", detail={"foo": "bar"}),
                Event(name="event1", detail={"baz": "qux"}),
            ]
        )


def test_trigger_events_multiple_duplicates_raises_error():
    """Test that multiple duplicate event names are all reported."""
    with pytest.raises(ValueError, match="Duplicate event names found"):
        TriggerEvents(
            [
                Event(name="event1"),
                Event(name="event2"),
                Event(name="event1"),
                Event(name="event2"),
            ]
        )


def test_trigger_events_single_convenience_method(state_address, execution_results):
    """Test TriggerEvents.single() convenience method."""
    trigger = TriggerEvents.single(
        name="notification",
        detail={"message": "Success!"},
    )
    trigger.process(state_address, execution_results)

    assert "HX-Trigger" in execution_results.response_headers
    header_value = json.loads(execution_results.response_headers["HX-Trigger"])
    assert header_value == {"notification": {"message": "Success!"}}


def test_trigger_events_single_with_target(state_address, execution_results):
    """Test TriggerEvents.single() with target selector."""
    trigger = TriggerEvents.single(
        name="update",
        detail={"count": 10},
        target="#counter",
    )
    trigger.process(state_address, execution_results)

    assert "HX-Trigger" in execution_results.response_headers
    header_value = json.loads(execution_results.response_headers["HX-Trigger"])
    assert header_value == {"update": {"count": 10, "target": "#counter"}}


def test_trigger_events_single_with_trigger_type(state_address, execution_results):
    """Test TriggerEvents.single() with custom trigger type."""
    trigger = TriggerEvents.single(
        name="afterSettle",
        trigger=Trigger.AFTER_SETTLE,
    )
    trigger.process(state_address, execution_results)

    assert "HX-Trigger-After-Settle" in execution_results.response_headers
    header_value = json.loads(
        execution_results.response_headers["HX-Trigger-After-Settle"]
    )
    assert header_value == {"afterSettle": {}}


def test_trigger_events_single_no_detail(state_address, execution_results):
    """Test TriggerEvents.single() without detail."""
    trigger = TriggerEvents.single(name="simpleEvent")
    trigger.process(state_address, execution_results)

    assert "HX-Trigger" in execution_results.response_headers
    header_value = json.loads(execution_results.response_headers["HX-Trigger"])
    assert header_value == {"simpleEvent": {}}


def test_trigger_events_serialization():
    """Test the serialize_events method."""
    trigger = TriggerEvents(
        [
            Event(name="event1", detail={"key": "value"}),
            Event(name="event2", target="#elem"),
        ]
    )
    serialized = trigger.serialize_events()
    assert serialized == {
        "event1": {"key": "value"},
        "event2": {"target": "#elem"},
    }
