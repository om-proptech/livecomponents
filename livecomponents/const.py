# The full ID look like this:
# "parent-type:parent-id/child-type:child-id"

#  HTMX doesn't escape query selectors, so elsewhere in the code we
# have to explicitly oass the escape the "hx-swap-oob" attributes
# as "hx-swap-oob="morph:#parent-type\:parent-id\/child-type\:child-id"
# https://github.com/bigskysoftware/htmx/issues/1537

HIER_SEP = "/"
TYPE_SEP = ":"
