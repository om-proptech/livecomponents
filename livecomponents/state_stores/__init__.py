from functools import cache

from livecomponents.state_stores.interface import IStateStore
from livecomponents.state_stores.redis import RedisStateStore


@cache
def get_default_state_store() -> IStateStore:
    return RedisStateStore()
