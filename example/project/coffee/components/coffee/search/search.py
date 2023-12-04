from django_components import component
from pydantic import BaseModel

from livecomponents import CallContext, InitStateContext, LiveComponent, command


class SearchState(BaseModel):
    pass


@component.register("coffee/search")
class SearchComponent(LiveComponent[SearchState]):
    template_name = "coffee/search/search.html"

    def init_state(self, context: InitStateContext, **component_kwargs) -> SearchState:
        return SearchState(**component_kwargs)

    @command
    def update_search(self, call_context: CallContext[SearchState], search: str):
        call_context.parent.update_search(search=search)
