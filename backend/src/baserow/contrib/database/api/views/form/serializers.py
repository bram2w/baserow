from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.api.user_files.serializers import UserFileField
from baserow.contrib.database.api.fields.serializers import FieldSerializer
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.views.models import (
    FormView,
    FormViewFieldOptions,
    FormViewFieldOptionsCondition,
    FormViewFieldOptionsConditionGroup,
)


class FormViewFieldOptionsConditionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormViewFieldOptionsConditionGroup
        fields = ("id", "filter_type")
        extra_kwargs = {"id": {"read_only": False}}


class FormViewFieldOptionsConditionSerializer(serializers.ModelSerializer):
    field = serializers.IntegerField(required=True, source="field_id")
    group = serializers.IntegerField(required=False, allow_null=True, source="group_id")

    class Meta:
        model = FormViewFieldOptionsCondition
        fields = ("id", "field", "type", "value", "group")
        extra_kwargs = {"id": {"read_only": False}}


class FormViewFieldOptionsSerializer(serializers.ModelSerializer):
    conditions = FormViewFieldOptionsConditionSerializer(many=True, required=False)
    condition_groups = FormViewFieldOptionsConditionGroupSerializer(
        many=True, required=False
    )

    class Meta:
        model = FormViewFieldOptions
        fields = (
            "name",
            "description",
            "enabled",
            "required",
            "show_when_matching_conditions",
            "condition_type",
            "order",
            "conditions",
            "condition_groups",
            "field_component",
        )


class PublicFormViewFieldSerializer(FieldSerializer):
    class Meta:
        model = Field
        fields = (
            "id",
            "type",
        )


class PublicFormViewFieldOptionsSerializer(FieldSerializer):
    field = serializers.SerializerMethodField(
        help_text="The properties of the related field. These can be used to construct "
        "the correct input. Additional properties could be added depending on the "
        "field type."
    )
    name = serializers.SerializerMethodField(
        help_text="If provided, then this value will be visible above the field input.",
    )
    conditions = FormViewFieldOptionsConditionSerializer(many=True, required=False)
    condition_groups = FormViewFieldOptionsConditionGroupSerializer(
        many=True, required=False
    )
    groups = FormViewFieldOptionsConditionGroupSerializer(many=True, required=False)

    class Meta:
        model = FormViewFieldOptions
        fields = (
            "name",
            "description",
            "required",
            "order",
            "field",
            "show_when_matching_conditions",
            "condition_type",
            "conditions",
            "condition_groups",
            "groups",
            "field_component",
        )

    # @TODO show correct API docs discriminated by field type.
    @extend_schema_field(PublicFormViewFieldSerializer)
    def get_field(self, instance):
        return field_type_registry.get_serializer(
            instance.field, PublicFormViewFieldSerializer
        ).data

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, instance):
        return instance.name or instance.field.name


class PublicFormViewSerializer(serializers.ModelSerializer):
    cover_image = UserFileField(
        help_text="The user file cover image that is displayed at the top of the form.",
    )
    logo_image = UserFileField(
        help_text="The user file logo image that is displayed at the top of the form.",
    )
    fields = PublicFormViewFieldOptionsSerializer(
        many=True, source="active_field_options"
    )
    show_logo = serializers.BooleanField(required=False)

    class Meta:
        model = FormView
        fields = (
            "title",
            "description",
            "mode",
            "cover_image",
            "logo_image",
            "submit_text",
            "fields",
            "show_logo",
        )


class FormViewSubmittedSerializer(serializers.ModelSerializer):
    row_id = serializers.IntegerField()

    class Meta:
        model = FormView
        fields = (
            "submit_action",
            "submit_action_message",
            "submit_action_redirect_url",
            "row_id",
        )


class FormViewNotifyOnSubmitSerializerMixin(serializers.Serializer):
    receive_notification_on_submit = serializers.SerializerMethodField(
        help_text="A boolean indicating if the current user should be notified when "
        "the form is submitted."
    )

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_receive_notification_on_submit(self, obj):
        logged_user_id = self.context["user"].id
        for usr in obj.users_to_notify_on_submit.all():
            if usr.id == logged_user_id:
                return True
        return False

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)

        receive_notification = data.get("receive_notification_on_submit", None)
        if receive_notification is not None:
            if not isinstance(receive_notification, bool):
                raise serializers.ValidationError(
                    "The value must be a boolean indicating if the current user should be "
                    "notified on submit or not."
                )
            ret["receive_notification_on_submit"] = receive_notification

        return ret
