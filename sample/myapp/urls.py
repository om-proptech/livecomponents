from django.urls import path

from sample.myapp.views import index

app_name = "myapp"

urlpatterns = [
    path("", index, name="index"),
]
