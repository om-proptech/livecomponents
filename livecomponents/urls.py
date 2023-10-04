from django.urls import path

from livecomponents.views import call_method

app_name = "livecomponents"

urlpatterns = [
    path("call_method/", call_method, name="call-method"),
]
