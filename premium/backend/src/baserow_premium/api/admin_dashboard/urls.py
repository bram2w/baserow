from django.conf.urls import url

from baserow_premium.api.admin_dashboard.views import AdminDashboardView


app_name = "baserow_premium.api.admin_dashboard"

urlpatterns = [
    url(r"^$", AdminDashboardView.as_view(), name="dashboard"),
]
