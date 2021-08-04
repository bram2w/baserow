from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import CharField

from baserow_premium.row_comments.models import RowComment

User = get_user_model()


class RowCommentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=32, source="user.first_name")
    own_comment = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_own_comment(self, object):
        return object.user == self.context["user"]

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
            "own_comment",
        )


class RowCommentCreateSerializer(serializers.ModelSerializer):
    comment = CharField(max_length=settings.MAX_ROW_COMMENT_LENGTH)

    class Meta:
        model = RowComment
        fields = ("comment",)
