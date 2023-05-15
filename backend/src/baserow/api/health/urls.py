from django.http import HttpResponse
from django.urls import re_path

from baserow.api.health.views import EmailTesterView, FullHealthCheckView

app_name = "baserow.api.health"


def public_health_check(request):
    return HttpResponse("OK")


urlpatterns = [
    re_path(r"full/$", FullHealthCheckView.as_view(), name="full_health_check"),
    re_path(r"email/$", EmailTesterView.as_view(), name="email_tester"),
    re_path("^$", public_health_check, name="public_health_check"),
]
