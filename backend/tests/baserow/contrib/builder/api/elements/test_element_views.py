from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from baserow.contrib.builder.elements.models import Element, LinkElement


@pytest.mark.django_db
def test_get_elements(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)
    element2 = data_fixture.create_builder_heading_element(page=page)
    element3 = data_fixture.create_builder_paragraph_element(page=page)

    url = reverse("api:builder:element:list", kwargs={"page_id": page.id})
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 3
    assert response_json[0]["id"] == element1.id
    assert response_json[0]["type"] == "heading"
    assert "level" in response_json[0]
    assert response_json[1]["id"] == element2.id
    assert response_json[1]["type"] == "heading"
    assert response_json[2]["id"] == element3.id
    assert response_json[2]["type"] == "paragraph"
    assert "level" not in response_json[2]


@pytest.mark.django_db
def test_create_element(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    url = reverse("api:builder:element:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": "heading"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "heading"
    assert response_json["value"] == ""

    response = api_client.post(
        url,
        {
            "type": "heading",
            "value": '"test"',
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["value"] == '"test"'


@pytest.mark.django_db
def test_create_element_bad_request(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    url = reverse("api:builder:element:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": "heading", "value": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_create_element_bad_request_for_formula(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    url = reverse("api:builder:element:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": "heading", "value": "not a formula"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"]["value"][0]["error"]
        == "The formula is invalid: Invalid syntax at line 1, col 3: missing '(' at ' '"
    )


@pytest.mark.django_db
def test_create_element_permission_denied(
    api_client, data_fixture, stub_check_permissions
):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    url = reverse("api:builder:element:list", kwargs={"page_id": page.id})
    with stub_check_permissions(raise_permission_denied=True):
        response = api_client.post(
            url,
            {"type": "heading"},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "PERMISSION_DENIED"


@pytest.mark.django_db
def test_create_element_page_does_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:builder:element:list", kwargs={"page_id": 0})
    response = api_client.post(
        url,
        {"type": "heading"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_PAGE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_update_element(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)

    url = reverse("api:builder:element:item", kwargs={"element_id": element1.id})
    response = api_client.patch(
        url,
        {"value": '"unusual suspect"', "level": 3},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["value"] == '"unusual suspect"'
    assert response.json()["level"] == 3


@pytest.mark.django_db
def test_update_element_bad_request(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)

    url = reverse("api:builder:element:item", kwargs={"element_id": element1.id})
    response = api_client.patch(
        url,
        {"value": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_update_element_does_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:builder:element:item", kwargs={"element_id": 0})
    response = api_client.patch(
        url,
        {"value": '"test"'},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ELEMENT_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_move_element_empty_payload(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)
    element2 = data_fixture.create_builder_heading_element(page=page)
    element3 = data_fixture.create_builder_heading_element(page=page)

    url = reverse("api:builder:element:move", kwargs={"element_id": element1.id})
    response = api_client.patch(
        url,
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    assert Element.objects.last().id == element1.id


@pytest.mark.django_db
def test_move_element_null_before_id(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)
    element2 = data_fixture.create_builder_heading_element(page=page)
    element3 = data_fixture.create_builder_heading_element(page=page)

    url = reverse("api:builder:element:move", kwargs={"element_id": element1.id})
    response = api_client.patch(
        url,
        {"before_id": None},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    assert Element.objects.last().id == element1.id


@pytest.mark.django_db
def test_move_element_before(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)
    element2 = data_fixture.create_builder_heading_element(page=page)
    element3 = data_fixture.create_builder_heading_element(page=page)

    url = reverse("api:builder:element:move", kwargs={"element_id": element3.id})
    response = api_client.patch(
        url,
        {"before_id": element2.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["id"] == element3.id

    assert list(Element.objects.all())[1].id == element3.id


@pytest.mark.django_db
def test_move_element_before_not_in_same_page(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    page2 = data_fixture.create_builder_page(user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)
    element2 = data_fixture.create_builder_heading_element(page=page)
    element3 = data_fixture.create_builder_heading_element(page=page2)

    url = reverse("api:builder:element:move", kwargs={"element_id": element3.id})
    response = api_client.patch(
        url,
        {"before_id": element2.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_ELEMENT_NOT_IN_SAME_PAGE"


@pytest.mark.django_db
def test_move_element_bad_before_id(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)

    url = reverse("api:builder:element:move", kwargs={"element_id": element1.id})
    response = api_client.patch(
        url,
        {"before_id": 9999},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_element(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)

    url = reverse("api:builder:element:item", kwargs={"element_id": element1.id})
    response = api_client.delete(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_delete_element_permission_denied(
    api_client, data_fixture, stub_check_permissions
):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    element1 = data_fixture.create_builder_heading_element(page=page)

    url = reverse("api:builder:element:item", kwargs={"element_id": element1.id})

    with stub_check_permissions(raise_permission_denied=True):
        response = api_client.delete(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "PERMISSION_DENIED"


@pytest.mark.django_db
def test_delete_element_element_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:builder:element:item", kwargs={"element_id": 0})
    response = api_client.delete(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ELEMENT_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_link_element_path_parameter_wrong_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    builder = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(builder=builder)
    page_with_params = data_fixture.create_builder_page(
        builder=builder,
        path="/test/:id",
        path_params=[{"name": "id", "type": "numeric"}],
    )

    link_element = data_fixture.create_builder_link_element(
        page=page,
        navigation_type=LinkElement.NAVIGATION_TYPES.PAGE,
        navigate_to_page=page_with_params,
    )

    url = reverse("api:builder:element:item", kwargs={"element_id": link_element.id})
    response = api_client.patch(
        url,
        {"page_parameters": [{"name": "id", "value": "not a number"}]},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    assert (
        response.json()["detail"]["page_parameters"][0]["value"][0]["error"]
        == "The formula is invalid: Invalid syntax at line 1, col 3: missing '(' at ' '"
    )


@pytest.mark.django_db
def test_can_move_element_inside_container(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    container_element = data_fixture.create_builder_column_element(page=page)
    element_one = data_fixture.create_builder_heading_element(
        page=page, parent_element=container_element, place_in_container="0"
    )
    element_two = data_fixture.create_builder_heading_element(
        page=page, parent_element=container_element, place_in_container="0"
    )

    assert element_two.parent_element is container_element
    assert element_two.place_in_container == "0"

    url = reverse("api:builder:element:move", kwargs={"element_id": element_two.id})
    response = api_client.patch(
        url,
        {
            "before_id": element_one.id,
            "parent_element_id": None,
            "place_in_container": None,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == 200

    element_two.refresh_from_db()

    assert element_two.parent_element is None
    assert element_two.place_in_container is None


@pytest.mark.django_db
def test_duplicate_element(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    element = data_fixture.create_builder_heading_element(user=user, value="'test'")

    url = reverse("api:builder:element:duplicate", kwargs={"element_id": element.id})
    response = api_client.post(url, HTTP_AUTHORIZATION=f"JWT {token}")

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["elements"][0]["id"] != element.id
    assert response_json["elements"][0]["value"] == element.value


@pytest.mark.django_db
def test_duplicate_element_does_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:builder:element:duplicate", kwargs={"element_id": 0})
    response = api_client.post(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ELEMENT_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_child_type_not_allowed_validation(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    parent = data_fixture.create_builder_form_container_element(page=page)

    url = reverse("api:builder:element:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": "button", "parent_element_id": parent.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
