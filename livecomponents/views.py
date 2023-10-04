from django.http import HttpRequest, HttpResponse


def call_method(request: HttpRequest):
    return HttpResponse("Hello")
