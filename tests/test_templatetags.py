import pytest

from livecomponents.templatetags.livecomponents import component_ancestor, component_id


def test_component_id():
    assert (
        component_id("table", "primary", "row", 1, "cell", "x")
        == "|table:primary|row:1|cell:x"
    )


@pytest.mark.parametrize(
    "ancestor_type, expected",
    [
        ("cell", "|table:primary|row:1|cell:x"),
        ("row", "|table:primary|row:1"),
        ("table", "|table:primary"),
        ("unknown", ""),
    ],
)
def test_component_ancestor(ancestor_type, expected):
    assert component_ancestor("|table:primary|row:1|cell:x", ancestor_type) == expected
