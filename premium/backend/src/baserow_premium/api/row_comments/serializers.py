from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from baserow_premium.row_comments.models import RowComment

User = get_user_model()


class RowCommentSerializer(ModelSerializer):
    first_name = CharField(max_length=32, source="user.first_name")

    class Meta:
        model = RowComment
        fields = (
            "id",
            "table",
            "row_id",
            "comment",
            "user",
            "first_name",
            "created_on",
            "updated_on",
        )


class RowCommentCreateSerializer(ModelSerializer):
    comment = CharField(max_length=settings.MAX_ROW_COMMENT_LENGTH)

    class Meta:
        model = RowComment
        fields = ("comment",)
