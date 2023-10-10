from django.urls import include, path

urlpatterns = [
    path("", include("project.myapp.urls")),
    path("coffee/", include("project.coffee.urls")),
    path("livecomponents/", include("livecomponents.urls")),
]
