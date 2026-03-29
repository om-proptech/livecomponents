# Decorators

LiveComponents provide a method decorator to ensure the user is authenticated.


```python
from livecomponents import LiveComponent, InitStateContext, CallContext
from livecomponents.decorators import livecomponents_login_required


class Something(LiveComponent):

    @livecomponents_login_required
    def init_state(self, context: InitStateContext):
        ...

    @livecomponents_login_required
    def do_something(self, call_context: CallContext[SomethingState], **kwargs):
        ...
```
