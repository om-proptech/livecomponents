from django.urls import include, path
from myapp.views import (
    chart,
    coffee,
    counters_index,
    modals,
    nestedcounter,
    registration,
    simplecounter,
    uploads,
    urlnavigation,
)

urlpatterns = [
    path("", counters_index, name="counters_index"),
    path("simplecounter/", simplecounter, name="simplecounter"),
    path("nestedcounter/", nestedcounter, name="nestedcounter"),
    path("coffee/", coffee, name="coffee"),
    path("modals/", modals, name="modals"),
    path("registration/", registration, name="registration"),
    path("uploads/", uploads, name="uploads"),
    path("chart/", chart, name="chart"),
    path("urlnavigation/", urlnavigation, name="urlnavigation"),
    path("livecomponents/", include("livecomponents.urls")),
]
