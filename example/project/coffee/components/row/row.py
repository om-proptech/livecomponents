from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django_components import component
from pydantic import BaseModel, ConfigDict

from livecomponents import CallContext, InitStateContext, LiveComponent, command
from livecomponents.manager.execution_results import ParentDirty
from project.coffee.models import CoffeeBean


class RowState(BaseModel):
    edit_mode: bool = False
    bean: CoffeeBean
    bean_form: ModelForm | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BeanForm(ModelForm):
    def clean_name(self):
        name = self.cleaned_data["name"]
        if name == "bad":
            raise ValidationError("Name cannot be bad")
        return name

    class Meta:
        model = CoffeeBean
        fields = ["name", "origin", "roast_level", "flavor_notes", "stock_quantity"]


@component.register("row")
class RowComponent(LiveComponent[RowState]):
    template_name = "row/row.html"

    def init_state(self, context: InitStateContext, **component_kwargs) -> RowState:
        return RowState(**component_kwargs)

    @command
    def edit_on(self, call_context: CallContext[RowState]):
        call_context.state.edit_mode = True
        if call_context.state.bean_form is None:
            call_context.state.bean_form = BeanForm(instance=call_context.state.bean)

    @command
    def edit_off(self, call_context: CallContext[RowState], **kwargs):
        call_context.state.edit_mode = False

    @command
    def edit(
        self,
        call_context: CallContext[RowState],
        **kwargs,
    ):
        bean_form = BeanForm(instance=call_context.state.bean, data=kwargs)
        if bean_form.is_valid():
            bean_form.save()
            call_context.state.bean_form = None
            call_context.state.edit_mode = False
        else:
            call_context.state.bean_form = bean_form

    @command
    def delete(self, call_context: CallContext[RowState]):
        call_context.state.bean.delete()
        return ParentDirty()

    @command
    def change_stock(self, call_context: CallContext[RowState], amount: int = 1):
        call_context.state.bean.stock_quantity += amount
        call_context.state.bean.save()
