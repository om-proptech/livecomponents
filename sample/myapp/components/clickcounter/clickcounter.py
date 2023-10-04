from django_components import component


@component.register("clickcounter")
class ClickCounter(component.Component):
    template_name = "clickcounter/clickcounter.html"

    def get_context_data(self):
        return {"value": 0}
