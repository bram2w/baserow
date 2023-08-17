from django.urls import re_path

from baserow.contrib.builder.api.theme.views import ThemeView

app_name = "baserow.contrib.builder.api.theme"

urlpatterns_with_builder_id = [
    re_path(
        r"$",
        ThemeView.as_view(),
        name="update",
    ),
]
