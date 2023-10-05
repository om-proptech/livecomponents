# We would love to use HIER_SEP = "/" and TYPE_SEP = ":"
# so that the full ID look like this:
# "parent-type:parent-id/child-type:child-id"

# However, HTMX doesn't escape query selectors, so we're forced to use
# something else. See:
# https://github.com/bigskysoftware/htmx/issues/1537

HIER_SEP = "-CHILD-"
TYPE_SEP = "-ID-"
