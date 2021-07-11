from django.conf.urls import url

from .views import (
    RotateFormViewSlugView,
    SubmitFormViewView,
    FormViewLinkRowFieldLookupView,
)


app_name = "baserow.contrib.database.api.views.form"

urlpatterns = [
    url(
        r"(?P<view_id>[0-9]+)/rotate-slug/$",
        RotateFormViewSlugView.as_view(),
        name="rotate_slug",
    ),
    url(
        r"(?P<slug>[-\w]+)/submit/$",
        SubmitFormViewView.as_view(),
        name="submit",
    ),
    url(
        r"(?P<slug>[-\w]+)/link-row-field-lookup/(?P<field_id>[0-9]+)/$",
        FormViewLinkRowFieldLookupView.as_view(),
        name="link_row_field_lookup",
    ),
]
