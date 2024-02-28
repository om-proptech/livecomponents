from django.urls import path

from registration.views import index

app_name = "registration"

urlpatterns = [
    path("", index, name="index"),
]
