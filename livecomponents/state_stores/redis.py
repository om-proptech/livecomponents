from redis import Redis

from livecomponents.state_stores import IStateStore


class RedisStateStore(IStateStore):
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "livecomponents:",
    ):
        self.client = Redis.from_url(redis_url)  # type: ignore
        self.key_prefix = key_prefix

    def get_raw_component_state(
        self, session_id: str, component_id: str
    ) -> bytes | None:
        return self.client.hget(f"{self.key_prefix}:{session_id}", component_id)

    def set_raw_component_state(
        self, session_id: str, component_id: str, raw_state: bytes
    ) -> None:
        self.client.hset(f"{self.key_prefix}:{session_id}", component_id, raw_state)
