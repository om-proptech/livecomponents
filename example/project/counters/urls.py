from django.urls import path

from project.counters.views import index

app_name = "counters"

urlpatterns = [
    path("", index, name="index"),
]
