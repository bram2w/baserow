from django.urls import re_path

from .views import (
    AsyncInstallTemplateCompatView,
    InstallTemplateCompatView,
    TemplatesCompatView,
)

app_name = "baserow.api.templates"


urlpatterns = [
    re_path(
        r"install/(?P<group_id>[0-9]+)/(?P<template_id>[0-9]+)/$",
        InstallTemplateCompatView.as_view(),
        name="install",
    ),
    re_path(
        r"install/(?P<group_id>[0-9]+)/(?P<template_id>[0-9]+)/async/$",
        AsyncInstallTemplateCompatView.as_view(),
        name="install_async",
    ),
    re_path(r"$", TemplatesCompatView.as_view(), name="list"),
]
