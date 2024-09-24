## Management Commands

## `createlivecomponent`

### Description

The `createlivecomponent` command is used to quickly create a new livecomponent. This command generates the necessary Python and HTML files for the component.

### Arguments

#### Positional Arguments

- `app_name` (str): The name of the app. E.g., 'counters'.
- `component_name` (str): Component name in snake case. The name can use directory separator for creating namespaces. Normally, the first namespace is the app name. E.g., 'counters/click_counter'.

#### Optional Arguments

- `--class-name` (str): Optional class name for the component. E.g., 'ClickCounter'. If not given, the component name, converted to PascalCase, is used.
- `-f`, `--force` (bool): Overwrite existing files. Default is `False`.
- `--stateless` (bool): Create a stateless component. Default is `False`.
- `--minimal` (bool): Create a minimal component without any commands. Default is `False`.
- `--base-class` (str): Base class for the component. If not given, value from settings is used.



### Usage Examples

#### Basic Usage

```sh
python manage.py createlivecomponent counters counters/click_counter
```

This command will create the files:

- `counters/components/counters/click_counter/click_counter.py` (Python file with the component class)
- `counters/components/counters/click_counter/click_counter.html` (HTML template for the component)

#### Create Minimal Statless Component

```sh
python manage.py createlivecomponent counters counters/click_counter --stateless --minimal
```

### Settings Options

#### Base Class Name

The base class name for the component can be configured in the Django settings under the `LIVECOMPONENTS` configuration. Example:

```python
# myproject/utils.py
import abc
from typing import Generic
from livecomponents import LiveComponent, StatelessLiveComponent
from livecomponents.types import State


class MyLiveComponent(LiveComponent, abc.ABC, Generic[State]):
    class Media:
        js = ["myproject/livecomponent.js"]


class MyStatelessLiveComponent(StatelessLiveComponent):
    class Media:
        js = ["myproject/livecomponent.js"]
```

```python
# settings.py
LIVECOMPONENTS = {
    # ...
    # Settings for the "./manage.py createlivecomponent" command.
    "createlivecomponent": {
        "base_class": "myproject.utils.MyLiveComponent",
        "stateless_base_class": "myproject.utils.MyStatelessLiveComponent",
    },
}
```
