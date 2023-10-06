from django.db.models import Q
from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import CallContext
from sample.coffee.models import CoffeeBean


class TableState(BaseModel):
    search: str = ""

    class Config:
        arbitrary_types_allowed = True


@component.register("table")
class TableComponent(LiveComponent[TableState]):
    template_name = "table/table.html"

    def get_extra_context_data(self, state: TableState):
        if state.search:
            beans = CoffeeBean.objects.filter(
                Q(name__icontains=state.search)
                | Q(origin__icontains=state.search)
                | Q(roast_level__icontains=state.search)
                | Q(flavor_notes__icontains=state.search)
            )
        else:
            beans = CoffeeBean.objects.all()
        return {"beans": beans}

    @classmethod
    def init_state(cls, **component_kwargs) -> TableState:
        return TableState(**component_kwargs)

    @classmethod
    def update_search(cls, call_context: CallContext[TableState], search: str):
        call_context.state.search = search
