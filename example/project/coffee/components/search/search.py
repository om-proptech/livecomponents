from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import CallContext, InitStateContext


class SearchState(BaseModel):
    pass


@component.register("search")
class SearchComponent(LiveComponent[SearchState]):
    template_name = "search/search.html"

    @classmethod
    def init_state(cls, context: InitStateContext, **component_kwargs) -> SearchState:
        return SearchState(**component_kwargs)

    @classmethod
    def update_search(cls, call_context: CallContext[SearchState], search: str):
        call_context.parent.update_search(search=search)
