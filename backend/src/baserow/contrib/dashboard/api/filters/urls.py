from django.urls import path

from .options import DashboardFilterOptionsView
from .views import DashboardFiltersView, DashboardFilterView

app_name = "baserow.contrib.dashboard.api.filters"

urlpatterns = [
    path(
        "filters/<int:filter_id>/options/",
        DashboardFilterOptionsView.as_view(),
        name="options",
    ),
    path("<int:dashboard_id>/filters/", DashboardFiltersView.as_view(), name="list"),
    path("filters/<int:filter_id>/", DashboardFilterView.as_view(), name="item"),
]
