from django.shortcuts import reverse

from openapi_spec_validator import openapi_v30_spec_validator


def test_openapi_spec(api_client):
    response = api_client.get(reverse("api:json_schema"))

    # If no exception is raised the spec is valid
    openapi_v30_spec_validator.validate(response.json())
