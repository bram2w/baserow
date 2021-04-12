import pytest
from pytz import timezone
from unittest.mock import patch
from datetime import datetime
from freezegun import freeze_time

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from django.shortcuts import reverse
from django.contrib.auth import get_user_model

from rest_framework_jwt.settings import api_settings


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


User = get_user_model()


@pytest.mark.django_db
def test_token_auth(api_client, data_fixture):
    user = data_fixture.create_user(
        email="test@test.nl", password="password", first_name="Test1"
    )

    assert not user.last_login

    response = api_client.post(
        reverse("api:user:token_auth"),
        {"username": "no_existing@test.nl", "password": "password"},
        format="json",
    )
    json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert len(json["non_field_errors"]) > 0

    response = api_client.post(
        reverse("api:user:token_auth"),
        {"username": "test@test.nl", "password": "wrong_password"},
        format="json",
    )
    json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert len(json["non_field_errors"]) > 0

    with freeze_time("2020-01-01 12:00"):
        response = api_client.post(
            reverse("api:user:token_auth"),
            {"username": "test@test.nl", "password": "password"},
            format="json",
        )
        json = response.json()
        assert response.status_code == HTTP_200_OK
        assert "token" in json
        assert "user" in json
        assert json["user"]["username"] == "test@test.nl"
        assert json["user"]["first_name"] == "Test1"
        assert json["user"]["is_staff"] is False

    user.refresh_from_db()
    assert user.last_login == datetime(2020, 1, 1, 12, 00, tzinfo=timezone("UTC"))

    with freeze_time("2020-01-02 12:00"):
        response = api_client.post(
            reverse("api:user:token_auth"),
            {"username": " teSt@teSt.nL ", "password": "password"},
            format="json",
        )
        json = response.json()
        assert response.status_code == HTTP_200_OK
        assert "token" in json
        assert "user" in json
        assert json["user"]["username"] == "test@test.nl"
        assert json["user"]["first_name"] == "Test1"
        assert json["user"]["is_staff"] is False

    user.refresh_from_db()
    assert user.last_login == datetime(2020, 1, 2, 12, 00, tzinfo=timezone("UTC"))


@pytest.mark.django_db
def test_token_refresh(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    response = api_client.post(
        reverse("api:user:token_refresh"), {"token": "WRONG_TOKEN"}, format="json"
    )
    assert response.status_code == HTTP_400_BAD_REQUEST

    response = api_client.post(
        reverse("api:user:token_refresh"), {"token": token}, format="json"
    )
    assert response.status_code == HTTP_200_OK
    json = response.json()
    assert "token" in json
    assert "user" in json
    assert json["user"]["username"] == "test@test.nl"
    assert json["user"]["first_name"] == "Test1"
    assert json["user"]["is_staff"] is False

    with patch("rest_framework_jwt.utils.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2019, 1, 1, 1, 1, 1, 0)
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        response = api_client.post(
            reverse("api:user:token_refresh"), json={"token": token}
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
