from django.urls import path

from counters.views import index

app_name = "counters"

urlpatterns = [
    path("", index, name="index"),
]
