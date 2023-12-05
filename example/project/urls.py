from django.urls import include, path

urlpatterns = [
    path("", include("counters.urls")),
    path("coffee/", include("coffee.urls")),
    path("modals/", include("modals.urls")),
    path("uploads/", include("uploads.urls")),
    path("livecomponents/", include("livecomponents.urls")),
]
