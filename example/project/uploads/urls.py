from django.urls import path

from project.uploads.views import index

app_name = "uploads"

urlpatterns = [
    path("", index, name="index"),
]
