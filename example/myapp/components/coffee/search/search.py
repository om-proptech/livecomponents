from django_components import register

from livecomponents import CallContext, StatelessLiveComponent, command


@register("coffee/search")
class SearchComponent(StatelessLiveComponent):
    template_name = "coffee/search/search.html"

    @command
    def update_search(self, call_context: CallContext, search: str):
        call_context.parent.update_search(search=search)
