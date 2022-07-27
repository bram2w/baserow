from django.urls import re_path

from .views import GalleryViewView, PublicGalleryViewRowsView

app_name = "baserow.contrib.database.api.views.gallery"

urlpatterns = [
    re_path(r"(?P<view_id>[0-9]+)/$", GalleryViewView.as_view(), name="list"),
    re_path(
        r"(?P<slug>[-\w]+)/public/rows/$",
        PublicGalleryViewRowsView.as_view(),
        name="public_rows",
    ),
]
