from django_components import component

from livecomponents import StatelessLiveComponent


@component.register("nestedcounter/button")
class ButtonComponent(StatelessLiveComponent):
    template_name = "nestedcounter/button/button.html"
