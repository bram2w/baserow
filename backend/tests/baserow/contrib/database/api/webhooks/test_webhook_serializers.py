import pytest
from rest_framework.serializers import ValidationError
from baserow.contrib.database.api.webhooks.validators import url_validation


@pytest.mark.parametrize(
    "valid_url",
    ["http://google.de", "https://google.de", "https://heise.de/myendpoint"],
)
def test_valid_urls(valid_url):
    validated_url = url_validation(valid_url)
    assert validated_url == valid_url


@pytest.mark.parametrize(
    "invalid_url",
    [
        "https://192.168.172.1:4000",
        "http://localhost",
        "http://localhost:4000/endpoint",
    ],
)
def test_invalid_urls(invalid_url):
    with pytest.raises(ValidationError):
        url_validation(invalid_url)
