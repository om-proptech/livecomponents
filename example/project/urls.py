from django.urls import include, path

urlpatterns = [
    path("", include("project.counters.urls")),
    path("coffee/", include("project.coffee.urls")),
    path("livecomponents/", include("livecomponents.urls")),
    path("modals/", include("project.modals.urls")),
]
