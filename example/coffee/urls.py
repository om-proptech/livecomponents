from django.urls import path

from coffee.views import index

app_name = "coffee"

urlpatterns = [
    path("", index, name="index"),
]
