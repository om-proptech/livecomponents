from functools import cache

from livecomponents.manager.manager import StateManager
from livecomponents.manager.serializers import PickleStateSerializer
from livecomponents.manager.stores import RedisStateStore


@cache
def get_state_manager() -> StateManager:
    return StateManager(
        serializer=PickleStateSerializer(),
        store=RedisStateStore(),
    )
