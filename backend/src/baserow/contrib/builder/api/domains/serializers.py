from rest_framework import serializers

from baserow.contrib.builder.domains.models import Domain


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ("id", "domain_name", "order", "builder_id")
        extra_kwargs = {
            "id": {"read_only": True},
            "builder_id": {"read_only": True},
            "order": {"help_text": "Lowest first."},
        }


class CreateDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ("domain_name",)


class OrderDomainsSerializer(serializers.Serializer):
    domain_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="The ids of the domains in the order they are supposed to be set in",
    )
