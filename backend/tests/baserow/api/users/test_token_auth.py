from datetime import datetime
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from freezegun import freeze_time
from pytz import timezone
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_201_CREATED
from rest_framework_jwt.settings import api_settings

from baserow.core.models import UserLogEntry
from baserow.core.registries import plugin_registry, Plugin

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


User = get_user_model()


@pytest.mark.django_db
def test_token_auth(api_client, data_fixture):
    class TmpPlugin(Plugin):
        type = "tmp_plugin"
        called = False

        def user_signed_in(self, user):
            self.called = True

    plugin_mock = TmpPlugin()

    user = data_fixture.create_user(
        email="test@test.nl", password="password", first_name="Test1", is_active=True
    )

    assert not user.last_login

    response = api_client.post(
        reverse("api:user:token_auth"),
        {"username": "no_existing@test.nl", "password": "password"},
        format="json",
    )
    json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert json["non_field_errors"][0] == "Unable to log in with provided credentials."

    response = api_client.post(
        reverse("api:user:token_auth"),
        {"username": "test@test.nl", "password": "wrong_password"},
        format="json",
    )
    json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert json["non_field_errors"][0] == "Unable to log in with provided credentials."

    with patch.dict(plugin_registry.registry, {"tmp": plugin_mock}):
        with freeze_time("2020-01-01 12:00"):
            response = api_client.post(
                reverse("api:user:token_auth"),
                {"username": "test@test.nl", "password": "password"},
                format="json",
            )
            json = response.json()
            assert response.status_code == HTTP_201_CREATED
            assert "token" in json
            assert "user" in json
            assert json["user"]["username"] == "test@test.nl"
            assert json["user"]["first_name"] == "Test1"
            assert json["user"]["id"] == user.id
            assert json["user"]["is_staff"] is False
            assert plugin_mock.called

    user.refresh_from_db()
    assert user.last_login == datetime(2020, 1, 1, 12, 00, tzinfo=timezone("UTC"))

    logs = UserLogEntry.objects.all()
    assert len(logs) == 1
    assert logs[0].actor_id == user.id
    assert logs[0].action == "SIGNED_IN"
    assert logs[0].timestamp == datetime(2020, 1, 1, 12, 00, tzinfo=timezone("UTC"))

    with freeze_time("2020-01-02 12:00"):
        response = api_client.post(
            reverse("api:user:token_auth"),
            {"username": " teSt@teSt.nL ", "password": "password"},
            format="json",
        )
        json = response.json()
        assert response.status_code == HTTP_201_CREATED
        assert "token" in json
        assert "user" in json
        assert json["user"]["username"] == "test@test.nl"
        assert json["user"]["first_name"] == "Test1"
        assert json["user"]["id"] == user.id
        assert json["user"]["is_staff"] is False

    user.refresh_from_db()
    assert user.last_login == datetime(2020, 1, 2, 12, 0, tzinfo=timezone("UTC"))

    data_fixture.create_user(
        email="test2@test.nl", password="password", first_name="Test1", is_active=False
    )
    response = api_client.post(
        reverse("api:user:token_auth"),
        {"username": "test2@test.nl", "password": "password"},
        format="json",
    )
    json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert json["non_field_errors"][0] == "User account is disabled."


@pytest.mark.django_db
def test_token_refresh(api_client, data_fixture):
    class TmpPlugin(Plugin):
        type = "tmp_plugin"
        called = False

        def user_signed_in(self, user):
            self.called = True

    plugin_mock = TmpPlugin()

    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )

    response = api_client.post(
        reverse("api:user:token_refresh"), {"token": "WRONG_TOKEN"}, format="json"
    )
    assert response.status_code == HTTP_400_BAD_REQUEST

    with patch.dict(plugin_registry.registry, {"tmp": plugin_mock}):
        response = api_client.post(
            reverse("api:user:token_refresh"), {"token": token}, format="json"
        )
        assert response.status_code == HTTP_201_CREATED
        json = response.json()
        assert "token" in json
        assert "user" in json
        assert json["user"]["username"] == "test@test.nl"
        assert json["user"]["first_name"] == "Test1"
        assert json["user"]["id"] == user.id
        assert json["user"]["is_staff"] is False
        assert not plugin_mock.called

    with patch("rest_framework_jwt.utils.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2019, 1, 1, 1, 1, 1, 0)
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        response = api_client.post(
            reverse("api:user:token_refresh"), json={"token": token}
        )
        assert response.status_code == HTTP_400_BAD_REQUEST
