from django_components import register

from livecomponents import StatelessLiveComponent


@register("nestedcounter/button")
class ButtonComponent(StatelessLiveComponent):
    template_name = "nestedcounter/button/button.html"
