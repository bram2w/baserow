from django.urls import re_path

from .views import TemplatesView, InstallTemplateView


app_name = "baserow.api.templates"


urlpatterns = [
    re_path(
        r"install/(?P<group_id>[0-9]+)/(?P<template_id>[0-9]+)/$",
        InstallTemplateView.as_view(),
        name="install",
    ),
    re_path(r"$", TemplatesView.as_view(), name="list"),
]
