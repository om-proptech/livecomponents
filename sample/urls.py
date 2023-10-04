from django.urls import include, path

urlpatterns = [
    path("", include("sample.myapp.urls")),
    path("livecomponents/", include("livecomponents.urls")),
]
