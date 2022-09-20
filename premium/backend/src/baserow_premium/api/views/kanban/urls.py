from django.urls import re_path

from .views import KanbanViewView, PublicKanbanViewView

app_name = "baserow_premium.api.views.kanban"

urlpatterns = [
    re_path(r"(?P<view_id>[0-9]+)/$", KanbanViewView.as_view(), name="list"),
    re_path(
        r"(?P<slug>[-\w]+)/public/rows/$",
        PublicKanbanViewView.as_view(),
        name="public_rows",
    ),
]
