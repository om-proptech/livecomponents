from django.urls import path

from project.myapp.views import index

app_name = "myapp"

urlpatterns = [
    path("", index, name="index"),
]
