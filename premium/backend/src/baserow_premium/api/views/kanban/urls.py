from django.urls import re_path

from .views import KanbanViewView


app_name = "baserow_premium.api.views.kanban"

urlpatterns = [
    re_path(r"(?P<view_id>[0-9]+)/$", KanbanViewView.as_view(), name="list"),
]
