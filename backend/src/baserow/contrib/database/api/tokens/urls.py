from django.conf.urls import url

from .views import TokensView, TokenView


app_name = "baserow.contrib.database.api.tokens"

urlpatterns = [
    url(r"(?P<token_id>[0-9]+)/$", TokenView.as_view(), name="item"),
    url(r"$", TokensView.as_view(), name="list"),
]
