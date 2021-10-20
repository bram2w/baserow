from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.openapi import OpenApiTypes

from baserow_premium.license.models import License

User = get_user_model()


class PremiumLicenseSerializer(serializers.ModelSerializer):
    license_id = serializers.CharField(help_text="Unique identifier of the license.")
    is_active = serializers.BooleanField(
        help_text="Indicates if the backend deems the license valid."
    )
    valid_from = serializers.DateTimeField(
        help_text="From which timestamp the license becomes active."
    )
    valid_through = serializers.DateTimeField(
        help_text="Until which timestamp the license is active."
    )
    seats_taken = serializers.SerializerMethodField(
        help_text="The amount of users that are currently using the license."
    )
    seats = serializers.IntegerField(
        help_text="The maximum amount of users that can use the license."
    )
    product_code = serializers.CharField(
        help_text="The product code that indicates what the license unlocks."
    )
    issued_on = serializers.DateTimeField(
        help_text="The date when the license was issued. It could be that a new "
        "license is issued with the same `license_id` because it was updated. In that "
        "case, the one that has been issued last should be used."
    )
    issued_to_email = serializers.EmailField(
        help_text="Indicates to which email address the license has been issued."
    )
    issued_to_name = serializers.CharField(
        help_text="Indicates to whom the license has been issued."
    )

    class Meta:
        model = License
        fields = (
            "id",
            "license_id",
            "is_active",
            "last_check",
            "valid_from",
            "valid_through",
            "seats_taken",
            "seats",
            "product_code",
            "issued_on",
            "issued_to_email",
            "issued_to_name",
        )

    @extend_schema_field(OpenApiTypes.INT)
    def get_seats_taken(self, obj):
        return (
            obj.seats_taken if hasattr(obj, "seats_taken") else obj.users.all().count()
        )


class RegisterPremiumLicenseSerializer(serializers.Serializer):
    license = serializers.CharField(help_text="The license that you want to register.")


class PremiumLicenseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "email")


class PremiumLicenseWithUsersSerializer(PremiumLicenseSerializer):
    users = serializers.SerializerMethodField()

    class Meta(PremiumLicenseSerializer.Meta):
        fields = PremiumLicenseSerializer.Meta.fields + ("users",)

    @extend_schema_field(PremiumLicenseUserSerializer(many=True))
    def get_users(self, object):
        users = [user.user for user in object.users.all()]
        return PremiumLicenseUserSerializer(users, many=True).data


class PremiumLicenseUserLookupSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField(
        help_text="The name and the email " "address of the user."
    )

    class Meta:
        model = User
        fields = ("id", "value")

    @extend_schema_field(OpenApiTypes.STR)
    def get_value(self, object):
        return f"{object.first_name} ({object.email})"
