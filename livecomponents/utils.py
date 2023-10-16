from livecomponents.const import HIER_SEP, TYPE_SEP


def find_component_id(
    full_component_id: str | None,
    component_name: str,
    own_id: str,
    parent_id: str,
) -> str:
    """Generate component ID from the given parameters.

    If full_component_id is given, it is returned as-is.

    If not.

    Then, we use registered_name (a component name) and own ID (a component ID)
    to generate the "basename for the component ID" (e.g., "button.1").

    Finally, we use parent_id (a component ID) and the basename to generate
    the full component ID (e.g., "/form.0/button.1").
    """
    # Used to re-render the component
    if full_component_id is not None:
        if not full_component_id.startswith(HIER_SEP):
            raise ValueError(f"full_component_id must start with '{HIER_SEP}'")
        return full_component_id

    # Used to render the component for the first time
    basename = f"{component_name}{TYPE_SEP}{own_id}"
    return f"{parent_id}{HIER_SEP}{basename}"
