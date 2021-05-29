from django.conf.urls import url

from baserow_premium.api.admin.dashboard.views import AdminDashboardView


app_name = "baserow_premium.api.admin.dashboard"

urlpatterns = [
    url(r"^$", AdminDashboardView.as_view(), name="dashboard"),
]
