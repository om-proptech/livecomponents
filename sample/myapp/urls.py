from django.urls import path

from sample.myapp.views import index

urlpatterns = [
    path("", index, name="index"),
]
