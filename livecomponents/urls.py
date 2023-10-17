from django.urls import path

from livecomponents.views import call_method, clear_session

app_name = "livecomponents"

urlpatterns = [
    path("call_method/", call_method, name="call-method"),
    path("clear_session/", clear_session, name="clear-session"),
]
