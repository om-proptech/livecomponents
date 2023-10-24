import abc
import base64
import datetime
import hashlib

from redis import Redis

from livecomponents.types import StateAddress


class IStateStore(abc.ABC):
    @abc.abstractmethod
    def is_component_initialized(self, state_addr: StateAddress) -> bool:
        ...

    @abc.abstractmethod
    def save_state(self, state_addr: StateAddress, raw_state: bytes) -> None:
        ...

    @abc.abstractmethod
    def restore_state(self, state_addr: StateAddress) -> bytes | None:
        ...

    @abc.abstractmethod
    def save_context(self, state_addr: StateAddress, raw_context: bytes) -> None:
        ...

    @abc.abstractmethod
    def restore_context(self, state_addr: StateAddress) -> bytes | None:
        ...

    @abc.abstractmethod
    def save_component_template(
        self, state_addr: StateAddress, html_bytes: bytes
    ) -> None:
        ...

    @abc.abstractmethod
    def restore_component_template(self, state_addr: StateAddress) -> bytes | None:
        ...

    @abc.abstractmethod
    def clear_session(self, session_id: str) -> None:
        ...


class MemoryStateStore(IStateStore):
    """In-memory state store. Suitable for tests."""

    def __init__(self):
        self._store: dict[StateAddress, bytes] = {}
        self._context: dict[StateAddress, bytes] = {}
        self._components: dict[StateAddress, bytes] = {}

    def is_component_initialized(self, state_addr: StateAddress) -> bool:
        return state_addr in self._store

    def save_state(self, state_addr: StateAddress, raw_state: bytes) -> None:
        self._store[state_addr] = raw_state

    def restore_state(self, state_addr: StateAddress) -> bytes | None:
        return self._store.get(state_addr)

    def save_context(self, state_addr: StateAddress, raw_context: bytes) -> None:
        self._context[state_addr] = raw_context

    def restore_context(self, state_addr: StateAddress) -> bytes | None:
        return self._context.get(state_addr)

    def save_component_template(
        self, state_addr: StateAddress, html_bytes: bytes
    ) -> None:
        self._components[state_addr] = html_bytes

    def restore_component_template(self, state_addr: StateAddress) -> bytes | None:
        return self._components.get(state_addr)

    def clear_session(self, session_id: str) -> None:
        for state_addr in list(self._store.keys()):
            if state_addr.session_id == session_id:
                del self._store[state_addr]
        for state_addr in list(self._context.keys()):
            if state_addr.session_id == session_id:
                del self._context[state_addr]
        for state_addr in list(self._components.keys()):
            if state_addr.session_id == session_id:
                del self._components[state_addr]


class RedisStateStore(IStateStore):
    """Redis-based state store."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        state_prefix: str = "lc:states:",
        context_prefix: str = "lc:ctxs:",
        templates_prefix: str = "lc:templates:",
        template_cache_prefix: str = "lc:template_cache:",
        ttl: datetime.timedelta = datetime.timedelta(days=1),
    ):
        self.client = Redis.from_url(redis_url)  # type: ignore
        self.key_prefix = state_prefix
        self.context_prefix = context_prefix
        self.templates_prefix = templates_prefix
        self.template_cache_prefix = template_cache_prefix
        self.ttl = ttl

    def is_component_initialized(self, state_addr: StateAddress) -> bool:
        key_name = self._get_key_name(self.key_prefix, state_addr.session_id)
        return self.client.hexists(key_name, state_addr.component_id)

    def save_state(self, state_addr: StateAddress, raw_state: bytes) -> None:
        return self._save_by_prefix(state_addr, self.key_prefix, raw_state)

    def restore_state(self, state_addr: StateAddress) -> bytes | None:
        return self._restore_by_prefix(state_addr, self.key_prefix)

    def save_context(self, state_addr: StateAddress, raw_context: bytes) -> None:
        return self._save_by_prefix(state_addr, self.context_prefix, raw_context)

    def restore_context(self, state_addr: StateAddress) -> bytes | None:
        return self._restore_by_prefix(state_addr, self.context_prefix)

    def _save_by_prefix(
        self, state_addr: StateAddress, prefix: str, raw_state: bytes
    ) -> None:
        key_name = self._get_key_name(prefix, state_addr.session_id)
        with self.client.pipeline() as pipe:
            pipe.hset(key_name, state_addr.component_id, raw_state)
            pipe.expire(key_name, self.ttl)
            pipe.execute()

    def _restore_by_prefix(self, state_addr: StateAddress, prefix: str) -> bytes | None:
        key_name = self._get_key_name(prefix, state_addr.session_id)
        with self.client.pipeline() as pipe:
            pipe.hget(key_name, state_addr.component_id)
            pipe.expire(key_name, self.ttl)
            raw_state, _ = pipe.execute()
        return raw_state

    def save_component_template(
        self, state_addr: StateAddress, html_bytes: bytes
    ) -> None:
        """Save serialized LiveComponentNode to Redis.

        Because live component nodes repeat themselves often, we cache them
        separately to avoid storing the same data multiple times.
        """
        hashed_value = self._get_hashed_value(html_bytes)
        cache_key = self._get_key_name(self.template_cache_prefix, hashed_value)
        nodes_key = self._get_key_name(self.templates_prefix, state_addr.session_id)
        with self.client.pipeline() as pipe:
            pipe.set(cache_key, html_bytes)
            pipe.expire(cache_key, self.ttl)

            pipe.hset(nodes_key, state_addr.component_id, hashed_value)
            pipe.expire(nodes_key, self.ttl)
            pipe.execute()

    def restore_component_template(self, state_addr: StateAddress) -> bytes | None:
        templates_key = self._get_key_name(self.templates_prefix, state_addr.session_id)
        with self.client.pipeline() as pipe:
            pipe.hget(templates_key, state_addr.component_id)
            pipe.expire(templates_key, self.ttl)
            hashed_value, _ = pipe.execute()
        if hashed_value is None:
            return None
        cache_key = self._get_key_name(
            self.template_cache_prefix, hashed_value.decode("ascii")
        )
        return self.client.get(cache_key)

    def clear_session(self, session_id: str) -> None:
        with self.client.pipeline() as pipe:
            pipe.delete(self._get_key_name(self.key_prefix, session_id))
            pipe.delete(self._get_key_name(self.templates_prefix, session_id))
            pipe.execute()

    @staticmethod
    def _get_key_name(key_prefix: str, session_id: str) -> str:
        return f"{key_prefix}{session_id}"

    @staticmethod
    def _get_hashed_value(value: bytes) -> str:
        return base64.urlsafe_b64encode(hashlib.md5(value).digest()).decode("ascii")[:8]
