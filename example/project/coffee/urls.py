from django.urls import path

from project.coffee.views import index

app_name = "coffee"

urlpatterns = [
    path("", index, name="index"),
]
