from django.conf import settings
from django.contrib.auth import get_user_model

from baserow_premium.row_comments.models import RowComment
from rest_framework import serializers
from rest_framework.fields import CharField

User = get_user_model()


class RowCommentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        max_length=32, source="user.first_name", required=False
    )
    edited = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()

    def get_edited(self, instance):
        return instance.updated_on > instance.created_on

    def get_comment(self, instance):
        # Ensure the comment content is not returned if it has been trashed
        if instance.trashed:
            return ""
        return instance.comment

    class Meta:
        model = RowComment
        fields = (
            "id",
            "table_id",
            "trashed",
            "row_id",
            "comment",
            "edited",
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
