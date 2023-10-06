# Sample

![Tests](https://github.com/imankulov/sample/actions/workflows/tests.yml/badge.svg)

Django Live Components sample

## On component IDs.

- Every component must have a root element that includes its ID. The id is "id={{ component_id }}".
- Component IDs represent the component hierarchy and formatted as absolute POSIX paths. For example, we can have a component /form.0/button.submit where "button" is the component type, "submit" is its name, and "form.0" is its parent.


## On component states


The state is defined in a separate class. The state must include parameters, passed to the component as keyword arguments, so that the component gets all necessary information to re-render itself on partial render.

For example, given the template the alert component:

```html
<alert>{{ message }}</alert>
```

that you want to use as

```
{% component "alert" message="Hello, world!" %}
```

Assuming that the component will be re-rendered on partial render, the state must include the "message" parameter:

```python
from pydantic import BaseModel
from livecomponents.component import LiveComponent

class AlertState(BaseModel):
    message: str = ""


class Alert(LiveComponent):

    template_name = "alert.html"


    @classmethod
    def init_state(cls, **component_kwargs) -> AlertState:
        return AlertState(**component_kwargs)
```

Component states don't need to be stored if components are not expected to be re-rendered independently, and only
as part of the parent component. For example, components for buttons are rarely re-rendered independently, so
you get away without the state model.

## On calling component methods from others

There are two ways to call component methods from other components:

Using the component ID. For example, if you have a component with ID "/message.0" and a method "set_message", you can call it like this:

```python
from livecomponents.manager.manager import CallContext

def do_something(call_context: CallContext):
    call_context.find_one("/message.0").set_message("Hello, world!")
```

Using the "parent" reference.

```python
from livecomponents.manager.manager import CallContext

def do_something(call_context: CallContext):
    call_context.parent.set_message("Hello, world!")
```
