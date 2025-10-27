from django.http import HttpRequest
from django.shortcuts import render
from pydantic import BaseModel


class SampleUser(BaseModel):
    username: str
    email: str


class UnpickleableObject:
    def __reduce__(self):
        raise TypeError("This object cannot be pickled")


def counters_index(request: HttpRequest):
    return render(
        request,
        "index.html",
        {
            "currency": "€",
        },
    )


def simplecounter(request: HttpRequest):
    return render(request, "simplecounter.html")


def nestedcounter(request: HttpRequest):
    return render(request, "nestedcounter.html")


def coffee(request: HttpRequest):
    return render(request, "coffee.html")


def modals(request: HttpRequest):
    users = [
        SampleUser(username="alice", email="alice@example.com"),
        SampleUser(username="bob", email="bob@example.com"),
        SampleUser(username="carol", email="carol@example.com"),
    ]
    return render(
        request, "modals.html", {"users": users, "unpickleable": UnpickleableObject()}
    )


def registration(request: HttpRequest):
    return render(request, "registration.html", {})


def uploads(request: HttpRequest):
    return render(request, "uploads.html", {})


def chart(request: HttpRequest):
    return render(request, "chart.html")


def urlnavigation(request: HttpRequest):
    return render(request, "urlnavigation.html")


def notification(request: HttpRequest):
    return render(request, "notification.html")
