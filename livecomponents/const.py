# The full ID look like this:
# "|parent-type:parent-id|child-type:child-id"
#
#
# A few things to note:
# - We use LiveComponentsPath() to parse it.
# - We intentionally don't use "/" as the hierarchy separator because we want to use
#   components that have "/" in their names. See "coffee/row" for example.
HIER_SEP = "|"
TYPE_SEP = ":"
DEFAULT_OWN_ID = "0"
