from django.urls import path

from project.modals.views import index

app_name = "modals"

urlpatterns = [
    path("", index, name="index"),
]
