# The full ID look like this:
# "parent-type.parent-id/child-type.child-id"

#  HTMX doesn't escape query selectors, so elsewhere in the code we
# have to explicitly oass the escape the "hx-swap-oob" attributes
# as "hx-swap-oob="morph:#parent-type\.parent-id\/child-type\.child-id"
# https://github.com/bigskysoftware/htmx/issues/1537

# We chose dot and slash as separators because this way we can leverage
# pathlib.PosixPath to parse it.
# We can use "stem" and "suffix" to get the component type and ID

HIER_SEP = "/"
TYPE_SEP = "."
