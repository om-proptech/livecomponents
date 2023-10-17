from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import CallContext, InitStateContext


class SearchState(BaseModel):
    pass


@component.register("search")
class SearchComponent(LiveComponent[SearchState]):
    template_name = "search/search.html"

    def init_state(self, context: InitStateContext, **component_kwargs) -> SearchState:
        return SearchState(**component_kwargs)

    def update_search(self, call_context: CallContext[SearchState], search: str):
        call_context.parent.update_search(search=search)
