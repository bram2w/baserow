from django.urls import path, re_path

from baserow.api.user_sources.views import (
    ListUserSourceUsersView,
    MoveUserSourceView,
    UserSourceBlacklistJSONWebToken,
    UserSourceForceObtainJSONWebToken,
    UserSourceObtainJSONWebToken,
    UserSourceRolesView,
    UserSourcesView,
    UserSourceTokenRefreshView,
    UserSourceView,
)
from baserow.core.app_auth_providers.registries import app_auth_provider_type_registry

app_name = "baserow.api.user_sources"

urlpatterns = [
    re_path(
        r"application/(?P<application_id>[0-9]+)/user-sources/$",
        UserSourcesView.as_view(),
        name="list",
    ),
    re_path(
        r"application/(?P<application_id>[0-9]+)/user-sources/roles/$",
        UserSourceRolesView.as_view(),
        name="list_roles",
    ),
    re_path(
        r"application/(?P<application_id>[0-9]+)/list-user-source-users/$",
        ListUserSourceUsersView.as_view(),
        name="list_user_source_users",
    ),
    re_path(
        r"user-source/(?P<user_source_id>[0-9]+)/$",
        UserSourceView.as_view(),
        name="item",
    ),
    re_path(
        r"user-source/(?P<user_source_id>[0-9]+)/move/$",
        MoveUserSourceView.as_view(),
        name="move",
    ),
    re_path(
        r"user-source/(?P<user_source_id>[0-9]+)/token-auth$",
        UserSourceObtainJSONWebToken.as_view(),
        name="token_auth",
    ),
    re_path(
        r"user-source/(?P<user_source_id>[0-9]+)/force-token-auth$",
        UserSourceForceObtainJSONWebToken.as_view(),
        name="force_token_auth",
    ),
    path(
        "user-source-auth-refresh/",
        UserSourceTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "user-source-token-blacklist/",
        UserSourceBlacklistJSONWebToken.as_view(),
        name="token_blacklist",
    ),
] + app_auth_provider_type_registry.api_urls
