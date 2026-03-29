from livecomponents.types import StateAddress


def test_save_state_sets_ttl(redis_state_store):
    state_addr = StateAddress(session_id="session_id", component_id="|root:0")
    state = b"state"
    redis_state_store.save_state(state_addr, state)

    # A bit less than ttl
    state_key = get_state_key(redis_state_store, state_addr)
    assert (
        redis_state_store.client.ttl(state_key)
        > redis_state_store.ttl.total_seconds() - 10
    )


def test_clear_session_sets_ttl_gc(redis_state_store):
    session_id = "session_id"
    state_addr = StateAddress(session_id=session_id, component_id="|root:0")
    state = b"state"
    redis_state_store.save_state(state_addr, state)

    # A bit less than ttl_gc
    redis_state_store.clear_session(session_id)
    state_key = get_state_key(redis_state_store, state_addr)
    assert (
        redis_state_store.client.ttl(state_key)
        <= redis_state_store.ttl_gc.total_seconds()
    )


def test_clear_session_and_then_save_state_recovers_ttl(redis_state_store):
    session_id = "session_id"
    state_addr = StateAddress(session_id=session_id, component_id="|root:0")
    state = b"state"
    redis_state_store.save_state(state_addr, state)
    redis_state_store.clear_session(session_id)
    redis_state_store.save_state(state_addr, state)

    # A bit less than ttl again
    state_key = get_state_key(redis_state_store, state_addr)
    assert (
        redis_state_store.client.ttl(state_key)
        > redis_state_store.ttl.total_seconds() - 10
    )


def test_ensure_session_makes_session_discoverable(redis_state_store):
    session_id = "stateless-session"
    assert not redis_state_store.session_exists(session_id)
    redis_state_store.ensure_session(session_id)
    assert redis_state_store.session_exists(session_id)


def test_ensure_session_is_idempotent(redis_state_store):
    session_id = "stateless-session"
    redis_state_store.ensure_session(session_id)
    redis_state_store.ensure_session(session_id)
    assert redis_state_store.session_exists(session_id)


def test_ensure_session_does_not_overwrite_existing_state(redis_state_store):
    state_addr = StateAddress(session_id="session_id", component_id="|root:0")
    redis_state_store.save_state(state_addr, b"real-state")
    redis_state_store.ensure_session("session_id")
    assert redis_state_store.restore_state(state_addr) == b"real-state"


def test_ensure_session_sets_ttl(redis_state_store):
    session_id = "stateless-session"
    redis_state_store.ensure_session(session_id)
    state_key = redis_state_store._get_key_name(
        redis_state_store.key_prefix, session_id
    )
    assert (
        redis_state_store.client.ttl(state_key)
        > redis_state_store.ttl.total_seconds() - 10
    )


def get_state_key(redis_state_store, state_addr):
    return redis_state_store._get_key_name(
        redis_state_store.key_prefix, state_addr.session_id
    )
