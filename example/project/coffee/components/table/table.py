from django.db.models import Q
from django_components import component

from livecomponents import CallContext, InitStateContext, LiveComponent, command
from livecomponents.utils import LiveComponentsModel
from project.coffee.models import CoffeeBean


class TableState(LiveComponentsModel):
    search: str = ""


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

    def init_state(self, context: InitStateContext, **component_kwargs) -> TableState:
        return TableState(**component_kwargs)

    @command
    def update_search(self, call_context: CallContext[TableState], search: str):
        call_context.state.search = search
