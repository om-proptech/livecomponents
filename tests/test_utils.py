# LiveComponentsPath
from livecomponents.utils import LiveComponentsPath


def test_live_components_path():
    path = LiveComponentsPath("|foo:bar|baz:spam")
    assert path.stem == "baz"
    assert str(path.parent) == "|foo:bar"
    assert str(path.parent.parent) == "|"
