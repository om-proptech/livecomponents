# Decorators

LiveComponents provide a method decorator to ensure the user is authenticated.


```python
from livecomponents import LiveComponent, InitStateContext, CallContext
from livecomponents.decorators import livecomponents_login_required


class Something(LiveComponent):

    @classmethod
    @livecomponents_login_required
    def init_state(cls, context: InitStateContext):
        ...

    @classmethod
    @livecomponents_login_required
    def do_something(cls, call_context: CallContext[SomethingState], **kwargs):
        ...
```
