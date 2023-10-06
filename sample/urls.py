from django.urls import include, path

urlpatterns = [
    path("", include("sample.myapp.urls")),
    path("coffee/", include("sample.coffee.urls")),
    path("livecomponents/", include("livecomponents.urls")),
]
