# State Serialization

When the page is rendered for the first time, a new session is created, and each component is initialized with its state by calling the `init_state()` method.

The state is then serialized and stored in the session store. As long as the session remains the same (in other words, while the page is not reloaded), the state is reused.

The state is serialized using the `StateSerializer` class and saved in Redis.

> [!NOTE]
>
> **Session Storage Size Warning.**
> Livecomponents use Redis as the session store. Keep in mind that a new session is created for each page load for every client and is stored there for 24 hours by default. This means you should keep the state compact.

## PickleStateSerializer

To convert the object to a string, the `PickleStateSerializer` is used.

The serializer employs a custom pickler and is optimized to effectively store the most common types of data used in a Django app. More specifically:

- When serializing a Django model, only the model's name and primary key are stored. The serializer utilizes the persistent_id/persistent_load pickle mechanism.
- When serializing a Pydantic model, only the model's name and the values of the fields are stored.
- When serializing a Django form, only the form's class name, along with initial data and data, are stored.

## Serializing Dynamically Created Classes

> [!WARNING]
> This section is an advanced topic that most users do not need. It's only necessary if you create model forms dynamically.

By default, pickle does not support serializing classes created dynamically (that is, classes defined as a result of a function call). Creating classes from functions is uncommon, but in some rare cases, you may want to do this, for example, when creating Django model forms dynamically.

If you attempt to serialize a dynamically created class, you will encounter an error like this:

```
AttributeError: Can't pickle local object 'dynamic_user_form.<locals>.DynamicUserForm'
```

The common solution for serializing dynamically created classes is to use a custom reducer by overriding the `__reduce__` method (see [Python docs](https://docs.python.org/3/library/pickle.html#object.__reduce__)). However, since `PickleStateSerializer` overrides the reducer for certain classes (specifically, for Django forms, templates, and models), your custom reducer will not be called for them.

If you want to ensure the use of your custom reducer, you must decorate it with the `livecomponents_reducer` decorator.

Here's the complete example:

```python
from django.forms import ModelForm
from django.contrib.auth.models import User

from livecomponents.manager.serializers import livecomponents_reducer


def dynamic_user_form(form_fields: list[str]):
    """Dynamically create a ModelForm for the User model with specified fields."""

    class DynamicUserForm(ModelForm):
        class Meta:
            model = User
            fields = form_fields

        @livecomponents_reducer  # <--- This is the key!
        def __reduce__(self):
            data = self.data if self.is_bound else None
            constructor_kwargs = {
                "initial": self.initial,
                "data": data,
            }
            if hasattr(self, "instance"):
                constructor_kwargs["instance"] = self.instance
            return restore_dynamic_user_form, (form_fields, constructor_kwargs)

    return DynamicUserForm


def restore_dynamic_user_form(form_fields: list[str], constructor_kwargs: dict):
    """Restore the dynamic User form with specified fields."""
    instance = dynamic_user_form(form_fields)(**constructor_kwargs)
    instance.full_clean()
    return instance
```
