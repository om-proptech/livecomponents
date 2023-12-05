from django.http import HttpRequest
from django.shortcuts import render
from pydantic import BaseModel


class SampleUser(BaseModel):
    username: str
    email: str


class UnpickleableObject:
    def __reduce__(self):
        raise TypeError("This object cannot be pickled")


def index(request: HttpRequest):
    users = [
        SampleUser(username="alice", email="alice@example.com"),
        SampleUser(username="bob", email="bob@example.com"),
        SampleUser(username="carol", email="carol@example.com"),
    ]
    return render(
        request, "modals.html", {"users": users, "unpickleable": UnpickleableObject()}
    )
