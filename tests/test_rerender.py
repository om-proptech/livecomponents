"""Tests for standalone command re-renders of components.

On a command call, the component is re-rendered outside of its original page,
from the template source saved in the state store. These tests cover the
regressions that are specific to this flow.
"""
from types import SimpleNamespace

from django.template import RequestContext, Template
from django_components import register

from livecomponents import (
    ExtraContextRequest,
    InitStateContext,
    LiveComponent,
)
from livecomponents.const import HIER_SEP, TYPE_SEP
from livecomponents.manager.manager import CallContext
from livecomponents.types import StateAddress
from livecomponents.utils import LiveComponentsModel
from livecomponents.views import re_render_component


class EmptyState(LiveComponentsModel):
    pass


@register("tests_echo")
class EchoComponent(LiveComponent[EmptyState]):
    """Echoes the "label" tag kwarg, so tests can see what kwargs resolve to."""

    template = (
        "{% load livecomponents %}"
        "<div {% component_attrs component_id %}>[{{ label }}]</div>"
    )

    def init_state(self, context: InitStateContext) -> EmptyState:
        return EmptyState()

    def get_extra_context_data(
        self, extra_context_request: ExtraContextRequest[EmptyState]
    ) -> dict:
        kwargs = extra_context_request.component_kwargs
        return {"label": kwargs.get("label", "MISSING")}


@register("tests_iso_child")
class IsolationChildComponent(LiveComponent[EmptyState]):
    template = (
        "{% load livecomponents %}"
        "<span {% component_attrs component_id %}>CHILD</span>"
    )

    def init_state(self, context: InitStateContext) -> EmptyState:
        return EmptyState()


@register("tests_iso_parent")
class IsolationParentComponent(LiveComponent[EmptyState]):
    """A component that uses session-dependent tags inside its template."""

    template = (
        "{% load livecomponents %}"
        "<div {% component_attrs component_id %}>"
        "<a href='{% call_command component_id \"noop\" %}'>cmd</a>"
        '{% livecomponent "tests_iso_child" parent_id=component_id %}'
        "</div>"
    )

    def init_state(self, context: InitStateContext) -> EmptyState:
        return EmptyState()


@register("tests_iso_sc_parent")
class IsolationSaveContextParent(LiveComponent[EmptyState]):
    """A component nesting a livecomponent with save_context."""

    template = (
        "{% load livecomponents %}"
        "<div {% component_attrs component_id %}>"
        '{% livecomponent "tests_echo" parent_id=component_id own_id="inner" '
        'label=greeting save_context="greeting" %}'
        "</div>"
    )

    def init_state(self, context: InitStateContext) -> EmptyState:
        return EmptyState()

    def get_extra_context_data(
        self, extra_context_request: ExtraContextRequest[EmptyState]
    ) -> dict:
        return {"greeting": "HELLO"}


def _rerender(rf, state_manager, state_address: StateAddress) -> str:
    request = rf.get("/")
    call_context: CallContext = CallContext(
        request=request,
        state=state_manager.get_component_state(state_address),
        state_address=state_address,
        state_manager=state_manager,
    )
    return re_render_component(call_context=call_context, state_address=state_address)


def test_nested_block_rerender(rf, state_manager):
    """A livecomponent_block nested in another block's fill must survive
    a re-render of the outer component.

    Regression test: the saved template source of the outer block used to be
    truncated at the inner block's end tag, making the re-render fail with
    TemplateSyntaxError.
    """
    session_id = "rerender-nested"
    page = Template(
        "{% load livecomponents component_tags %}"
        '{% livecomponent_block "sample" own_id="outer" message="out" %}'
        '{% fill "body" %}OUTERFILL'
        '{% livecomponent_block "sample" own_id="inner" message="in" %}'
        '{% fill "body" %}INNERFILL{% endfill %}'
        "{% endlivecomponent_block %}"
        "{% endfill %}"
        "{% endlivecomponent_block %}"
    )
    request = rf.get("/")
    first_render = page.render(
        RequestContext(
            request,
            {"request": request, "LIVECOMPONENTS_SESSION_ID": session_id},
        )
    )
    assert "OUTERFILL" in first_render
    assert "INNERFILL" in first_render

    outer_addr = StateAddress(
        session_id=session_id,
        component_id=f"{HIER_SEP}sample{TYPE_SEP}outer",
    )

    # The saved source of the outer component must be balanced: it must
    # contain both the inner and the outer end tags.
    saved_source = state_manager.restore_component_template(outer_addr)
    assert saved_source.count("{% endlivecomponent_block %}") == 2

    re_rendered = _rerender(rf, state_manager, outer_addr)
    assert "OUTERFILL" in re_rendered
    assert "INNERFILL" in re_rendered


def test_rerender_resolves_kwargs_against_restored_context(rf, state_manager):
    """Tag kwargs referencing saved context vars must survive a re-render.

    Regression test for two related bugs:

    - Tag kwargs used to be resolved against the minimal re-render context
      (where page variables don't exist) instead of the restored one, so the
      component received empty kwargs on re-renders.
    - When save_context was passed as a template variable, the restore step
      was skipped entirely on re-renders (the variable resolves to "" there).
    """
    session_id = "rerender-kwargs"
    page = Template(
        "{% load livecomponents %}"
        '{% livecomponent "tests_echo" own_id="e" '
        "label=account.name save_context=vars_csv %}"
    )
    request = rf.get("/")
    first_render = page.render(
        RequestContext(
            request,
            {
                "request": request,
                "LIVECOMPONENTS_SESSION_ID": session_id,
                "account": SimpleNamespace(name="ACME"),
                "vars_csv": "account",
            },
        )
    )
    assert "[ACME]" in first_render

    echo_addr = StateAddress(
        session_id=session_id,
        component_id=f"{HIER_SEP}tests_echo{TYPE_SEP}e",
    )
    re_rendered = _rerender(rf, state_manager, echo_addr)
    assert "[ACME]" in re_rendered


def test_isolated_context_rendering(rf, state_manager):
    """Live components support the `only` isolation flag.

    Regression test: session-dependent tags (nested {% livecomponent %},
    {% call_command %}) inside an isolated component template used to raise
    KeyError for LIVECOMPONENTS_SESSION_ID.
    """
    session_id = "rerender-isolated"
    page = Template(
        "{% load livecomponents %}"
        '{% livecomponent "tests_iso_parent" own_id="p" only %}'
    )
    request = rf.get("/")
    rendered = page.render(
        RequestContext(
            request,
            {"request": request, "LIVECOMPONENTS_SESSION_ID": session_id},
        )
    )
    assert "CHILD" in rendered
    assert f"session_id={session_id}" in rendered


def test_isolated_rerender_with_nested_save_context(rf, state_manager):
    """save_context on a component nested in an isolated (only) template
    must survive a re-render of the outer component.

    Regression test: the restore branch of save_or_restore_context() read
    "request" and "LIVECOMPONENTS_SESSION_ID" directly from the context.
    Both keys are absent inside an isolated context, so the first command
    re-render raised KeyError: 'LIVECOMPONENTS_SESSION_ID'.
    """
    session_id = "rerender-iso-save-context"
    page = Template(
        "{% load livecomponents %}"
        '{% livecomponent "tests_iso_sc_parent" own_id="p" only %}'
    )
    request = rf.get("/")
    first_render = page.render(
        RequestContext(
            request,
            {"request": request, "LIVECOMPONENTS_SESSION_ID": session_id},
        )
    )
    assert "[HELLO]" in first_render

    parent_addr = StateAddress(
        session_id=session_id,
        component_id=f"{HIER_SEP}tests_iso_sc_parent{TYPE_SEP}p",
    )
    re_rendered = _rerender(rf, state_manager, parent_addr)
    assert "[HELLO]" in re_rendered
