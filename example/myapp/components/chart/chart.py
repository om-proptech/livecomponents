import random
from typing import Any, Literal

from django_components import component
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from livecomponents import (
    ExtraContextRequest,
    LiveComponent,
    LiveComponentsModel,
    command,
)
from livecomponents.manager.manager import CallContext, InitStateContext


class ChartDataPoint(BaseModel):
    label: str
    value: float


class ChartState(LiveComponentsModel):
    data: list[ChartDataPoint] = Field(default_factory=list)
    chart_type: Literal["bar", "line"] = Field(default="bar")
    chart_slug: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


@component.register("chart")
class ChartComponent(LiveComponent[ChartState]):
    template_name = "chart/chart.html"

    def get_extra_context_data(
        self, extra_context_request: ExtraContextRequest[ChartState]
    ) -> dict[str, Any]:
        # Export the entire state to the client side, and save it in a JSON script
        # to initialize or update the chart.
        return {
            "json_script_id": f"chart_state_{extra_context_request.state.chart_slug}",
            "chart_state": extra_context_request.state.model_dump(by_alias=True),
        }

    def init_state(self, context: InitStateContext) -> ChartState:
        return ChartState(
            chart_slug="main_chart",
            data=[
                ChartDataPoint(label="January", value=65),
                ChartDataPoint(label="February", value=59),
                ChartDataPoint(label="March", value=80),
                ChartDataPoint(label="April", value=81),
                ChartDataPoint(label="May", value=56),
                ChartDataPoint(label="June", value=55),
            ],
        )

    @command
    def add_data_point(self, call_context: CallContext[ChartState]):
        """Add a new data point to the chart."""
        months = ["July", "August", "September", "October", "November", "December"]
        available_months = [
            m for m in months if not any(d.label == m for d in call_context.state.data)
        ]

        if available_months:
            new_month = available_months[0]
            new_value = random.randint(30, 100)
            call_context.state.data.append(
                ChartDataPoint(label=new_month, value=new_value)
            )

    @command
    def remove_last_point(self, call_context: CallContext[ChartState]):
        """Remove the last data point from the chart."""
        if call_context.state.data:
            call_context.state.data.pop()

    @command
    def change_chart_type(self, call_context: CallContext[ChartState]):
        """Toggle between bar and line chart types."""
        current_type = call_context.state.chart_type
        call_context.state.chart_type = "line" if current_type == "bar" else "bar"

    @command
    def randomize_data(self, call_context: CallContext[ChartState]):
        """Randomize all chart values."""
        for data_point in call_context.state.data:
            data_point.value = random.randint(20, 100)
