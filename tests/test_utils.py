import pytest

from livecomponents.utils import LiveComponentsPath, get_ancestor_id


def test_live_components_path():
    path = LiveComponentsPath("|foo:bar|baz:spam")
    assert path.stem == "baz"
    assert str(path.parent) == "|foo:bar"
    assert str(path.parent.parent) == "|"


@pytest.mark.parametrize(
    "ancestor_type,expected_ancestor_id",
    [
        ("bar", "|foo:1|bar:2"),
        ("foo", "|foo:1"),
        ("spam", None),
        ("", None),
    ],
)
def test_get_ancestor_id(ancestor_type, expected_ancestor_id):
    assert get_ancestor_id("|foo:1|bar:2|baz:3", ancestor_type) == expected_ancestor_id
