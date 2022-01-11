from django.urls import re_path

from .views import SubmitFormViewView


app_name = "baserow.contrib.database.api.views.form"

urlpatterns = [
    re_path(
        r"(?P<slug>[-\w]+)/submit/$",
        SubmitFormViewView.as_view(),
        name="submit",
    ),
]
