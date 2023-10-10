from functools import cache

from livecomponents.manager.manager import StateManager
from livecomponents.settings import get_config


@cache
def get_state_manager() -> StateManager:
    config = get_config()
    return StateManager(
        serializer=config.state_serializer.get_instance(),
        store=config.state_store.get_instance(),
    )
