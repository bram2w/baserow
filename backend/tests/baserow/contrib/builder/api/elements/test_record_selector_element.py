from django.urls import reverse

import pytest

from baserow.contrib.builder.elements.models import RecordSelectorElement


@pytest.mark.django_db
def test_record_selector_element_api_rejects_schema_property(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    record_selector_element = data_fixture.create_builder_element(
        RecordSelectorElement, user, page
    )

    url = reverse(
        "api:builder:element:list",
        kwargs={"page_id": record_selector_element.page.id},
    )
    response = api_client.get(url, format="json", HTTP_AUTHORIZATION=f"JWT {token}")
    for element in response.json():
        assert "schema_property" not in element

    url = reverse(
        "api:builder:element:item",
        kwargs={"element_id": record_selector_element.id},
    )
    response = api_client.patch(
        url,
        {"fields": [{"schema_property": "INVALID"}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert "schema_property" not in response.json()
