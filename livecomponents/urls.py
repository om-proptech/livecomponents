from django.urls import path

from livecomponents.views import call_command, clear_session

app_name = "livecomponents"

urlpatterns = [
    path("call_command/", call_command, name="call-command"),
    path("clear_session/", clear_session, name="clear-session"),
]
