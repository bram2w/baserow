from typing import Callable
from django.conf import settings

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import is_valid_path

from rest_framework import status


def json_error_404_add_trailing_slash(path: str) -> HttpResponse:
    """
    Return a nicer and informative error in case the url is
    valid adding a trailing slash to the end.
    The same error message is returned both for safe method that
    could be redirected (GET, HEAD, OPTIONS) and for unsafe methods
    where redirection with data is not possible due to security limitations.
    """

    return JsonResponse(
        {
            "error": "URL_TRAILING_SLASH_MISSING",
            "detail": (
                "A valid URL must end with a trailing slash. "
                f"Please, redirect requests to {path}/"
            ),
        },
        status=status.HTTP_404_NOT_FOUND,
    )


def json_error_404_not_found(path: str) -> HttpResponse:
    return JsonResponse(
        {"error": "URL_NOT_FOUND", "detail": f"URL {path} not found."},
        status=status.HTTP_404_NOT_FOUND,
    )


def json_is_accepted(request: HttpRequest) -> bool:
    accept_headers = request.headers.get("accept", "")
    return "application/json" in accept_headers or accept_headers in ["*/*", ""]


class BaserowCustomHttp404Middleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if response.status_code == 404:
            path, urlconf = request.path_info, getattr(request, "urlconf", None)
            if (
                is_valid_path(path, urlconf)
                or settings.DEBUG
                and not json_is_accepted(request)
            ):
                return response
            elif is_valid_path(f"{path}/", urlconf):
                return json_error_404_add_trailing_slash(path)
            else:
                return json_error_404_not_found(path)
        return response
