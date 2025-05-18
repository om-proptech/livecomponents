# Nested Livecomponents

While livecomponents can be used as standalone components, they can also be nested. This approach allows you to split complex user interfaces into smaller components and develop them independently.

Although you can create advanced nested livecomponents, there are several caveats to be aware of. We've found that it's much easier to reason about the livecomponents lifecycle using the "root with stateless children" pattern.

Let's explore this pattern in detail.

## Root with stateless children

The idea behind this pattern is to create a single component (typically called "myapp/root") that maintains the entire state and contains all the actions that can modify this state.

Child components are stateless and don't have any actions. Their Django templates call the actions defined in their root component.

While this approach makes the root and child components tightly coupled (you can't use child components independently), it makes the data flow easier to understand. Additionally, all logic is concentrated in a single place.

## Nested Counter Example

Let's start by creating a view and a template that renders the root component.

```python
# counters/views.py

def nestedcounter(request: HttpRequest):
    return render(request, "nestedcounter.html")
```

```django
# templates/nestedcounter.html

{% extends "base.html" %}
{% load livecomponents %}

{% block body %}
  <h1>Nested counter</h1>
  {% livecomponent "nestedcounter/root" %}
{% endblock %}
```

Since the nested counter components don't exist yet, let's first create a placeholder for the root component. We'll create a root component that will maintain the counter state.

```shell
./manage.py createlivecomponent counters nestedcounter/root ./manage.py
```

Now, let's modify the root component to define the state and action.

```python
class RootState(LiveComponentsModel):
    value: int = 0


@component.register("nestedcounter/root")
class RootComponent(LiveComponent[RootState]):

    ...

    @command
    def increment(self, call_context: CallContext[RootState], value: int):
        """Increment the counter."""
        call_context.state.value += value
```

In this simple example, we could create both the current value display and the increment button in the same template like this:

```django
{% load livecomponents %}

<div {% component_attrs component_id %}>
    Counter: {{ value }}
    <button {% component_attrs component_id %}
        hx-post='{% call_command component_id "increment" %}'
        hx-vals='{"value": 1}'
    >
        +1
    </button>
</div>
```

However, for demonstration purposes, let's extract the button into a separate stateless component.

Let's update the root component's HTML to use the new button component:

```django
{% load livecomponents %}

<div {% component_attrs component_id %}>
    Counter: {{ value }}
    {% livecomponent "nestedcounter/button" parent_id=component_id %}
</div>
```

!!! info "The `parent_id` argument"

    The `parent_id=component_id` argument is crucial for building the component hierarchy. It passes the ID of the parent component to the child component, establishing their relationship.

Now, let's create the button component placeholder:

```shell
createlivecomponent counters nestedcounter/button --stateless --minimal
```

The Python code for the button can remain minimal since it's stateless:

```python
from django_components import component

from livecomponents import StatelessLiveComponent


@component.register("nestedcounter/button")
class ButtonComponent(StatelessLiveComponent):
    template_name = "nestedcounter/button/button.html"
```

The HTML code will look like this:

```django
{% load livecomponents %}
{% component_ancestor component_id "nestedcounter/root" as root_id %}

<button {% component_attrs component_id %}
    hx-post='{% call_command root_id "increment" %}'
    hx-vals='{"value": 1}'
>
    +1
</button>
```

The key part is the `{% component_ancestor component_id "nestedcounter/root" as root_id %}` line. This allows the button component to call the `increment` command on the root component.

Note that if the parent component doesn't include the `parent_id=component_id` argument, the `component_ancestor` tag will return an empty string, and the command call will fail.

## Hierarchy Implementation Details

When rendering a page, the component hierarchy is stored in the livecomponent IDs, which remain stable across page loads.

For an isolated component, the ID format is simple:

```
|<component_type>:<own_id>
```

Here, `component_type` is the livecomponent name (like "my_button" or "nestedcounter/button"), and `own_id` is the component's ID. If no component ID is provided, it defaults to 0.

For hierarchical components, the ID encodes the entire hierarchy as a concatenation of the parent ID, component type, and component ID:

```
|<parent_type>:<parent_id>|...|<component_type>:<own_id>
```

This is where the `parent_id=component_id` argument comes into play - it passes the parent ID to build the full component ID for the child.

All other features, such as calling `parent` from the component or using the `component_ancestor` template tag, are convenience methods for working with the hierarchy. These functions and template tags parse the ID string similarly to how Python's `os.path` handles file paths.
