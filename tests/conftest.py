import os

import pytest

from livecomponents.manager import get_state_manager
from livecomponents.manager.stores import RedisStateStore

# Playwright runs the async loop which makes Django raising a SynchronousOnlyOperation
# exception. This is a workaround to allow async code in tests.
# See more, for example, in
# https://github.com/microsoft/playwright-python/issues/439#issuecomment-763339612
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@pytest.fixture
def state_manager():
    state_manager = get_state_manager()
    state_manager.store.clear_all_sessions()
    return state_manager


@pytest.fixture
def redis_state_store():
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        pytest.skip("Redis URL not provided")
    return RedisStateStore(redis_url=redis_url)
