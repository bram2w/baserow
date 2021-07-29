from django.conf.urls import url

from baserow_premium.api.row_comments.views import RowCommentView

app_name = "baserow_premium.api.row_comments"

urlpatterns = [
    url(
        r"^(?P<table_id>[0-9]+)/(?P<row_id>[0-9]+)/$",
        RowCommentView.as_view(),
        name="item",
    ),
]
