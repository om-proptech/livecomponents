import abc

from redis import Redis

from livecomponents.types import StateAddress


class IStateStore(abc.ABC):
    @abc.abstractmethod
    def restore(self, state_addr: StateAddress) -> bytes | None:
        ...

    @abc.abstractmethod
    def save(self, state_addr: StateAddress, raw_state: bytes) -> None:
        ...


class RedisStateStore(IStateStore):
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "livecomponents:",
    ):
        self.client = Redis.from_url(redis_url)  # type: ignore
        self.key_prefix = key_prefix

    def restore(self, state_addr: StateAddress) -> bytes | None:
        return self.client.hget(
            f"{self.key_prefix}:{state_addr.session_id}", state_addr.component_id
        )

    def save(self, state_addr: StateAddress, raw_state: bytes) -> None:
        self.client.hset(
            f"{self.key_prefix}:{state_addr.session_id}",
            state_addr.component_id,
            raw_state,
        )
