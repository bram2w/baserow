from typing import Callable

from django.http import HttpRequest, HttpResponse

from opentelemetry import baggage, context
from opentelemetry.trace import get_current_span


class BaserowOTELMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        span = get_current_span()
        attrs = getattr(span, "_attributes", {})
        http_route = attrs.get("http.route")
        if http_route:
            context.attach(baggage.set_baggage("http.route", http_route))
