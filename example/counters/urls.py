from django.urls import path

from counters.views import index, nestedcounter, simplecounter

app_name = "counters"

urlpatterns = [
    path("", index, name="index"),
    path("simplecounter/", simplecounter, name="simplecounter"),
    path("nestedcounter/", nestedcounter, name="nestedcounter"),
]
