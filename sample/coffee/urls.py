from django.urls import path

from sample.coffee.views import index

app_name = "coffee"

urlpatterns = [
    path("", index, name="index"),
]
