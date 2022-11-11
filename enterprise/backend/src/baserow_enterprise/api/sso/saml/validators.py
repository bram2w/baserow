import io

from rest_framework import serializers
from saml2.xml.schema import XMLSchemaError
from saml2.xml.schema import validate as validate_saml_metadata_schema

from baserow_enterprise.sso.saml.exceptions import SamlProviderForDomainAlreadyExists
from baserow_enterprise.sso.saml.models import SamlAuthProviderModel


def validate_unique_saml_domain(
    domain, instance=None, model_class=SamlAuthProviderModel
):
    queryset = model_class.objects.filter(domain=domain)
    if instance:
        queryset = queryset.exclude(id=instance.id)
    if queryset.exists():
        raise SamlProviderForDomainAlreadyExists(
            f"There is already a {model_class.__name__} for this domain."
        )
    return domain


def validate_saml_metadata(value):
    metadata = io.StringIO(value)
    try:
        validate_saml_metadata_schema(metadata)
    except XMLSchemaError:
        raise serializers.ValidationError(
            "The metadata is not valid according to the XML schema."
        )

    return value
