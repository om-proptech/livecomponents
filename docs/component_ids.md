# Component IDs

- Every component must have a root element that includes its ID. The ID is `id={{ component_id }}`.
- Component IDs represent the component hierarchy and are formatted as "|parent:id|child:id". For example, we can have a component |form:0|button:submit where "button" is the component type, "submit" is its name, and "form:0" is its parent.

In many contexts, you get access to the StateAddress object, which consists of the session ID and the component ID.
In this pair, the component ID is a "ComponentId" instance (a subclass of str), which has a helpful method
to create child items.

It can be used like this, without explicitly setting the child own_id:

    state_address.component_id | "child_component"

Or like this, with explicitly setting the child own_id:

    state_address.component_id | ("child_component", "child_own_id")
