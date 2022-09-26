from rest_framework import serializers


class UpdatePremiumViewAttributesSerializer(serializers.Serializer):
    show_logo = serializers.BooleanField(required=False)
