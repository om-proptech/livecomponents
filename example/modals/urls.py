from django.urls import path

from modals.views import index

app_name = "modals"

urlpatterns = [
    path("", index, name="index"),
]
