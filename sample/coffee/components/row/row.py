from django_components import component
from pydantic import BaseModel

from livecomponents import LiveComponent
from livecomponents.manager.manager import CallContext
from sample.coffee.models import CoffeeBean


class RowState(BaseModel):
    edit_mode: bool = False
    bean: CoffeeBean

    class Config:
        arbitrary_types_allowed = True


class BeanEditInput(BaseModel):
    name: str
    origin: str
    roast_level: str
    flavor_notes: str
    stock_quantity: int

    def update_bean(self, bean: CoffeeBean):
        bean.name = self.name
        bean.origin = self.origin
        bean.roast_level = self.roast_level
        bean.flavor_notes = self.flavor_notes
        bean.stock_quantity = self.stock_quantity
        bean.save()


@component.register("row")
class RowComponent(LiveComponent[RowState]):
    template_name = "row/row.html"

    @classmethod
    def init_state(cls, **component_kwargs) -> RowState:
        return RowState(**component_kwargs)

    @classmethod
    def edit_on(cls, call_context: CallContext[RowState]):
        call_context.state.edit_mode = True

    @classmethod
    def edit_off(cls, call_context: CallContext[RowState], **kwargs):
        call_context.state.edit_mode = False

    @classmethod
    def edit(
        cls,
        call_context: CallContext[RowState],
        **kwargs,
    ):
        bean_edit_input = BeanEditInput(**kwargs)
        bean_edit_input.update_bean(call_context.state.bean)
        call_context.state.edit_mode = False
