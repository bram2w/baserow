from django.conf.urls import url

from rest_framework_jwt.views import refresh_jwt_token, verify_jwt_token

from .views import (
    UserView, SendResetPasswordEmailView, ResetPasswordView, ObtainJSONWebToken
)


app_name = 'baserow.api.v0.user'

urlpatterns = [
    url(r'^token-auth/$', ObtainJSONWebToken.as_view(), name='token_auth'),
    url(r'^token-refresh/$', refresh_jwt_token, name='token_refresh'),
    url(r'^token-verify/$', verify_jwt_token, name='token_verify'),
    url(
        r'^send-reset-password-email/$',
        SendResetPasswordEmailView.as_view(),
        name='send_reset_password_email'
    ),
    url(
        r'^reset-password/$',
        ResetPasswordView.as_view(),
        name='reset_password'
    ),
    url(r'^$', UserView.as_view(), name='index')
]
