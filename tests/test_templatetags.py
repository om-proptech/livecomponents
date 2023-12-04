from livecomponents.templatetags.livecomponents import component_id


def test_component_id():
    assert (
        component_id("table", "primary", "row", 1, "cell", "x")
        == "|table:primary|row:1|cell:x"
    )
