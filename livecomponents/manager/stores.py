import abc
import datetime

from redis import Redis

from livecomponents.types import StateAddress


class IStateStore(abc.ABC):
    @abc.abstractmethod
    def restore(self, state_addr: StateAddress) -> bytes | None:
        ...

    @abc.abstractmethod
    def save(self, state_addr: StateAddress, raw_state: bytes) -> None:
        ...


class MemoryStateStore(IStateStore):
    """In-memory state store. Suitable for tests."""

    def __init__(self):
        self._store: dict[StateAddress, bytes] = {}

    def restore(self, state_addr: StateAddress) -> bytes | None:
        return self._store.get(state_addr)

    def save(self, state_addr: StateAddress, raw_state: bytes) -> None:
        self._store[state_addr] = raw_state


class RedisStateStore(IStateStore):
    """Redis-based state store."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "livecomponents:",
        ttl: datetime.timedelta = datetime.timedelta(days=1),
    ):
        self.client = Redis.from_url(redis_url)  # type: ignore
        self.key_prefix = key_prefix
        self.ttl = ttl

    def restore(self, state_addr: StateAddress) -> bytes | None:
        key_name = self._get_key_name(state_addr.session_id)
        with self.client.pipeline() as pipe:
            pipe.hget(key_name, state_addr.component_id)
            pipe.expire(key_name, self.ttl)
            raw_state, _ = pipe.execute()
        return raw_state

    def save(self, state_addr: StateAddress, raw_state: bytes) -> None:
        key_name = self._get_key_name(state_addr.session_id)
        with self.client.pipeline() as pipe:
            pipe.hset(key_name, state_addr.component_id, raw_state)
            pipe.expire(key_name, self.ttl)
            pipe.execute()

    def _get_key_name(self, session_id: str) -> str:
        return f"{self.key_prefix}{session_id}"
