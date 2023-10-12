import os

# Playwright runs the async loop which makes Django raising a SynchronousOnlyOperation
# exception. This is a workaround to allow async code in tests.
# See more, for example, in
# https://github.com/microsoft/playwright-python/issues/439#issuecomment-763339612
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
