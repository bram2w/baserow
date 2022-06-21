from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.fields import CharField

from baserow_premium.row_comments.models import RowComment

User = get_user_model()


class RowCommentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        max_length=32, source="user.first_name", required=False
    )

    class Meta:
        model = RowComment
        fields = (
            "id",
            "table_id",
            "row_id",
            "comment",
            "first_name",
            "created_on",
            "updated_on",
            "user_id",
        )


class RowCommentCreateSerializer(serializers.ModelSerializer):
    comment = CharField(max_length=settings.MAX_ROW_COMMENT_LENGTH)

    class Meta:
        model = RowComment
        fields = ("comment",)
