"""
API tests for the Markdown text format of the form element labels and the
choice element option names. The format is stored inside the value itself, as
a `__markdown__` marker in front of the formula or name, so it goes through the
regular formula validation.
"""

from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from baserow.core.formula.text_format import MARKDOWN_PREFIX

LABEL_ELEMENT_TYPES = [
    "input_text",
    "choice",
    "checkbox",
    "rating_input",
    "datetime_picker",
    "record_selector",
]


@pytest.mark.django_db
@pytest.mark.parametrize("element_type", LABEL_ELEMENT_TYPES)
def test_create_element_with_markdown_label(api_client, data_fixture, element_type):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    label = f"{MARKDOWN_PREFIX}concat('**', get('page_parameter.id'), '**')"

    url = reverse("api:builder:element:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": element_type, "label": {"formula": label, "mode": "simple"}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["label"]["formula"] == label


@pytest.mark.django_db
@pytest.mark.parametrize("element_type", LABEL_ELEMENT_TYPES)
def test_update_element_markdown_label_is_still_validated(
    api_client, data_fixture, element_type
):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    url = reverse("api:builder:element:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": element_type},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    element_id = response.json()["id"]

    url = reverse("api:builder:element:item", kwargs={"element_id": element_id})
    response = api_client.patch(
        url,
        {"label": {"formula": f"{MARKDOWN_PREFIX}'**Bold**'", "mode": "simple"}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["label"]["formula"] == f"{MARKDOWN_PREFIX}'**Bold**'"

    # The marker does not bypass the validation of the formula behind it.
    response = api_client.patch(
        url,
        {
            "label": {
                "formula": f"{MARKDOWN_PREFIX}get('foobar.123')",
                "mode": "simple",
            }
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"]["label"][0]["code"] == "invalid_formula_argument"


@pytest.mark.django_db
def test_choice_element_markdown_option_names(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    url = reverse("api:builder:element:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {
            "type": "choice",
            "options": [
                {"name": f"{MARKDOWN_PREFIX}**Bold**", "value": None},
                {"name": "Plain", "value": "plain"},
            ],
            "formula_name": {
                "formula": f"{MARKDOWN_PREFIX}get('data_source.1.*.field_2')",
                "mode": "simple",
            },
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert [(o["name"], o["value"]) for o in response_json["options"]] == [
        (f"{MARKDOWN_PREFIX}**Bold**", None),
        ("Plain", "plain"),
    ]
    assert response_json["formula_name"]["formula"] == (
        f"{MARKDOWN_PREFIX}get('data_source.1.*.field_2')"
    )
