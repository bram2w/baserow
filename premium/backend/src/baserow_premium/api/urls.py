from django.urls import path, include

from .user_admin import urls as user_admin_urls


app_name = "baserow_premium.api"

urlpatterns = [
    path("admin/user/", include(user_admin_urls, namespace="admin_user")),
]
