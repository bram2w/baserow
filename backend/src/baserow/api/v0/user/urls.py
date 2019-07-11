from django.conf.urls import url

from rest_framework_jwt.views import (
    obtain_jwt_token, refresh_jwt_token, verify_jwt_token
)

from .views import UserView


app_name = 'baserow.api.v0.user'

urlpatterns = [
    url(r'^token-auth/$', obtain_jwt_token, name='token_auth'),
    url(r'^token-refresh/$', refresh_jwt_token, name='token_refresh'),
    url(r'^token-verify/$', verify_jwt_token, name='token_verify'),
    url(r'^$', UserView.as_view(), name='index')
]
