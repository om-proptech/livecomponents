from django_components import component

from livecomponents import (
    LiveComponent,
    LiveComponentsModel,
    command,
)
from livecomponents.manager.execution_results import ComponentDirty, PushUrl, ReplaceUrl


class UrlnavigationState(LiveComponentsModel):
    current_page: str = "page1"
    navigation_count: int = 0


@component.register("urlnavigation")
class UrlnavigationComponent(LiveComponent[UrlnavigationState]):
    template_name = "urlnavigation/urlnavigation.html"

    def init_state(self, context):
        return UrlnavigationState()

    @command
    def navigate_push(self, call_context, page: str):
        call_context.state.current_page = page
        call_context.state.navigation_count += 1
        return [ComponentDirty(), PushUrl(f"/urlnavigation/?page={page}")]

    @command
    def navigate_replace(self, call_context, page: str):
        call_context.state.current_page = page
        call_context.state.navigation_count += 1
        return [ComponentDirty(), ReplaceUrl(f"/urlnavigation/?page={page}")]
