import os
import pytest
from freezegun import freeze_time
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.conf import settings

from baserow.contrib.database.models import Database, Table
from baserow.core.handler import CoreHandler
from baserow.core.models import Group, GroupUser
from baserow.core.user.handler import UserHandler

User = get_user_model()


@pytest.mark.django_db
def test_create_user(client, data_fixture):
    valid_password = "thisIsAValidPassword"
    short_password = "short"
    response = client.post(
        reverse("api:user:index"),
        {"name": "Test1", "email": "test@test.nl", "password": valid_password},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    user = User.objects.get(email="test@test.nl")
    assert user.first_name == "Test1"
    assert user.email == "test@test.nl"
    assert user.password != ""
    assert "password" not in response_json["user"]
    assert response_json["user"]["username"] == "test@test.nl"
    assert response_json["user"]["first_name"] == "Test1"
    assert response_json["user"]["is_staff"] is True

    response_failed = client.post(
        reverse("api:user:index"),
        {"name": "Test1", "email": "test@test.nl", "password": valid_password},
        format="json",
    )
    assert response_failed.status_code == 400
    assert response_failed.json()["error"] == "ERROR_EMAIL_ALREADY_EXISTS"

    response_failed = client.post(
        reverse("api:user:index"),
        {"name": "Test1", "email": " teSt@teST.nl ", "password": valid_password},
        format="json",
    )
    assert response_failed.status_code == 400
    assert response_failed.json()["error"] == "ERROR_EMAIL_ALREADY_EXISTS"

    data_fixture.update_settings(allow_new_signups=False)
    response_failed = client.post(
        reverse("api:user:index"),
        {"name": "Test1", "email": "test10@test.nl", "password": valid_password},
        format="json",
    )
    assert response_failed.status_code == 400
    assert response_failed.json()["error"] == "ERROR_DISABLED_SIGNUP"
    data_fixture.update_settings(allow_new_signups=True)

    response_failed_2 = client.post(
        reverse("api:user:index"), {"email": "test"}, format="json"
    )
    assert response_failed_2.status_code == 400

    long_password = "x" * 256
    response = client.post(
        reverse("api:user:index"),
        {"name": "Test2", "email": "test2@test.nl", "password": long_password},
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    user = User.objects.get(email="test2@test.nl")
    assert user.check_password(long_password)

    long_password = "x" * 257
    response = client.post(
        reverse("api:user:index"),
        {"name": "Test2", "email": "test2@test.nl", "password": long_password},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"]["password"][0]["code"] == "password_validation_failed"
    )
    assert (
        response_json["detail"]["password"][0]["error"]
        == "This password is too long. It must not exceed 256 characters."
    )

    response = client.post(
        reverse("api:user:index"),
        {"name": "Test2", "email": "random@test.nl", "password": short_password},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"]["password"][0]["code"] == "password_validation_failed"
    )
    assert (
        response_json["detail"]["password"][0]["error"]
        == "This password is too short. It must contain at least 8 characters."
    )


@pytest.mark.django_db
def test_create_user_with_invitation(data_fixture, client):
    core_handler = CoreHandler()
    valid_password = "thisIsAValidPassword"
    invitation = data_fixture.create_group_invitation(email="test0@test.nl")
    signer = core_handler.get_group_invitation_signer()

    response_failed = client.post(
        reverse("api:user:index"),
        {
            "name": "Test1",
            "email": "test@test.nl",
            "password": valid_password,
            "group_invitation_token": "INVALID",
        },
        format="json",
    )
    assert response_failed.status_code == HTTP_400_BAD_REQUEST
    assert response_failed.json()["error"] == "BAD_TOKEN_SIGNATURE"

    response_failed = client.post(
        reverse("api:user:index"),
        {
            "name": "Test1",
            "email": "test@test.nl",
            "password": valid_password,
            "group_invitation_token": signer.dumps(99999),
        },
        format="json",
    )
    assert response_failed.status_code == HTTP_404_NOT_FOUND
    assert response_failed.json()["error"] == "ERROR_GROUP_INVITATION_DOES_NOT_EXIST"

    response_failed = client.post(
        reverse("api:user:index"),
        {
            "name": "Test1",
            "email": "test@test.nl",
            "password": valid_password,
            "group_invitation_token": signer.dumps(invitation.id),
        },
        format="json",
    )
    assert response_failed.status_code == HTTP_400_BAD_REQUEST
    assert response_failed.json()["error"] == "ERROR_GROUP_INVITATION_EMAIL_MISMATCH"
    assert User.objects.all().count() == 1

    response_failed = client.post(
        reverse("api:user:index"),
        {
            "name": "Test1",
            "email": "test0@test.nl",
            "password": valid_password,
            "group_invitation_token": signer.dumps(invitation.id),
        },
        format="json",
    )
    assert response_failed.status_code == HTTP_200_OK
    assert User.objects.all().count() == 2
    assert Group.objects.all().count() == 1
    assert Group.objects.all().first().id == invitation.group_id
    assert GroupUser.objects.all().count() == 2
    assert Database.objects.all().count() == 0
    assert Table.objects.all().count() == 0


@pytest.mark.django_db
def test_create_user_with_template(data_fixture, client):
    old_templates = settings.APPLICATION_TEMPLATES_DIR
    valid_password = "thisIsAValidPassword"
    settings.APPLICATION_TEMPLATES_DIR = os.path.join(
        settings.BASE_DIR, "../../../tests/templates"
    )
    template = data_fixture.create_template(slug="example-template")

    response = client.post(
        reverse("api:user:index"),
        {
            "name": "Test1",
            "email": "test0@test.nl",
            "password": valid_password,
            "template_id": -1,
        },
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["template_id"][0]["code"] == "does_not_exist"

    response = client.post(
        reverse("api:user:index"),
        {
            "name": "Test1",
            "email": "test0@test.nl",
            "password": valid_password,
            "template_id": "random",
        },
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["template_id"][0]["code"] == "incorrect_type"

    response = client.post(
        reverse("api:user:index"),
        {
            "name": "Test1",
            "email": "test0@test.nl",
            "password": valid_password,
            "template_id": template.id,
        },
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    assert Group.objects.all().count() == 2
    assert GroupUser.objects.all().count() == 1
    # We expect the example template to be installed
    assert Database.objects.all().count() == 1
    assert Database.objects.all().first().name == "Event marketing"
    assert Table.objects.all().count() == 2

    settings.APPLICATION_TEMPLATES_DIR = old_templates


@pytest.mark.django_db(transaction=True)
def test_send_reset_password_email(data_fixture, client, mailoutbox):
    data_fixture.create_user(email="test@localhost.nl")

    response = client.post(
        reverse("api:user:send_reset_password_email"), {}, format="json"
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    response = client.post(
        reverse("api:user:send_reset_password_email"),
        {"email": "unknown@localhost.nl", "base_url": "http://localhost:3000"},
        format="json",
    )
    assert response.status_code == 204
    assert len(mailoutbox) == 0

    response = client.post(
        reverse("api:user:send_reset_password_email"),
        {"email": "test@localhost.nl", "base_url": "http://test.nl"},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_HOSTNAME_IS_NOT_ALLOWED"
    assert len(mailoutbox) == 0

    response = client.post(
        reverse("api:user:send_reset_password_email"),
        {"email": "test@localhost.nl", "base_url": "http://localhost:3000"},
        format="json",
    )
    assert response.status_code == 204
    assert len(mailoutbox) == 1

    response = client.post(
        reverse("api:user:send_reset_password_email"),
        {"email": " teST@locAlhost.nl ", "base_url": "http://localhost:3000"},
        format="json",
    )
    assert response.status_code == 204
    assert len(mailoutbox) == 2

    email = mailoutbox[0]
    assert "test@localhost.nl" in email.to
    assert email.body.index("http://localhost:3000")


@pytest.mark.django_db
def test_password_reset(data_fixture, client):
    user = data_fixture.create_user(email="test@localhost")
    handler = UserHandler()
    valid_password = "thisIsAValidPassword"
    short_password = "short"
    long_password = (
        "Bgvmt95en6HGJZ9Xz0F8xysQ6eYgo2Y54YzRPxxv10b5n16F4rZ6YH4ulonocwiFK6970KiAxoYhU"
        "LYA3JFDPIQGj5gMZZl25M46sO810Zd3nyBg699a2TDMJdHG7hAAi0YeDnuHuabyBawnb4962OQ1OO"
        "f1MxzFyNWG7NR2X6MZQL5G1V61x56lQTXbvK1AG1IPM87bQ3YAtIBtGT2vK3Wd83q3he5ezMtUfzK"
        "2ibj0WWhf86DyQB4EHRUJjYcBiI78iEJv5hcu33X2I345YosO66cTBWK45SqJEDudrCOq"
    )
    signer = handler.get_reset_password_signer()

    response = client.post(reverse("api:user:reset_password"), {}, format="json")
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    response = client.post(
        reverse("api:user:reset_password"),
        {"token": "test", "password": valid_password},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "BAD_TOKEN_SIGNATURE"

    with freeze_time("2020-01-01 12:00"):
        token = signer.dumps(user.id)

    with freeze_time("2020-01-04 12:00"):
        response = client.post(
            reverse("api:user:reset_password"),
            {"token": token, "password": valid_password},
            format="json",
        )
        response_json = response.json()
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response_json["error"] == "EXPIRED_TOKEN_SIGNATURE"

    with freeze_time("2020-01-01 12:00"):
        token = signer.dumps(9999)

    with freeze_time("2020-01-02 12:00"):
        response = client.post(
            reverse("api:user:reset_password"),
            {"token": token, "password": valid_password},
            format="json",
        )
        response_json = response.json()
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response_json["error"] == "ERROR_USER_NOT_FOUND"

    with freeze_time("2020-01-01 12:00"):
        token = signer.dumps(user.id)

    with freeze_time("2020-01-02 12:00"):
        response = client.post(
            reverse("api:user:reset_password"),
            {"token": token, "password": valid_password},
            format="json",
        )
        assert response.status_code == 204

    user.refresh_from_db()
    assert user.check_password(valid_password)

    with freeze_time("2020-01-02 12:00"):
        token = signer.dumps(user.id)

    with freeze_time("2020-01-02 12:00"):
        response = client.post(
            reverse("api:user:reset_password"),
            {"token": token, "password": short_password},
            format="json",
        )
        response_json = response.json()
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
        assert (
            response_json["detail"]["password"][0]["code"]
            == "password_validation_failed"
        )
        assert (
            response_json["detail"]["password"][0]["error"]
            == "This password is too short. It must contain at least 8 characters."
        )

    user.refresh_from_db()
    assert not user.check_password(short_password)

    with freeze_time("2020-01-02 12:00"):
        response = client.post(
            reverse("api:user:reset_password"),
            {"token": token, "password": long_password},
            format="json",
        )
        response_json = response.json()
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
        assert (
            response_json["detail"]["password"][0]["code"]
            == "password_validation_failed"
        )
        assert (
            response_json["detail"]["password"][0]["error"]
            == "This password is too long. It must not exceed 256 characters."
        )

    user.refresh_from_db()
    assert not user.check_password(long_password)


@pytest.mark.django_db
def test_change_password(data_fixture, client):
    valid_old_password = "thisIsAValidPassword"
    valid_new_password = "thisIsAValidNewPassword"
    short_password = "short"
    long_password = (
        "Bgvmt95en6HGJZ9Xz0F8xysQ6eYgo2Y54YzRPxxv10b5n16F4rZ6YH4ulonocwiFK6970KiAxoYhU"
        "LYA3JFDPIQGj5gMZZl25M46sO810Zd3nyBg699a2TDMJdHG7hAAi0YeDnuHuabyBawnb4962OQ1OO"
        "f1MxzFyNWG7NR2X6MZQL5G1V61x56lQTXbvK1AG1IPM87bQ3YAtIBtGT2vK3Wd83q3he5ezMtUfzK"
        "2ibj0WWhf86DyQB4EHRUJjYcBiI78iEJv5hcu33X2I345YosO66cTBWK45SqJEDudrCOq"
    )
    user, token = data_fixture.create_user_and_token(
        email="test@localhost", password=valid_old_password
    )

    response = client.post(
        reverse("api:user:change_password"),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    response = client.post(
        reverse("api:user:change_password"),
        {"old_password": "INCORRECT", "new_password": valid_new_password},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_INVALID_OLD_PASSWORD"

    user.refresh_from_db()
    assert user.check_password(valid_old_password)

    response = client.post(
        reverse("api:user:change_password"),
        {"old_password": valid_old_password, "new_password": short_password},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"]["new_password"][0]["code"]
        == "password_validation_failed"
    )
    assert (
        response_json["detail"]["new_password"][0]["error"]
        == "This password is too short. It must contain at least 8 characters."
    )

    user.refresh_from_db()
    assert user.check_password(valid_old_password)

    response = client.post(
        reverse("api:user:change_password"),
        {"old_password": valid_old_password, "new_password": long_password},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response_json["detail"]["new_password"][0]["code"]
        == "password_validation_failed"
    )
    assert (
        response_json["detail"]["new_password"][0]["error"]
        == "This password is too long. It must not exceed 256 characters."
    )

    user.refresh_from_db()
    assert user.check_password(valid_old_password)

    response = client.post(
        reverse("api:user:change_password"),
        {"old_password": valid_old_password, "new_password": valid_new_password},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == 204

    user.refresh_from_db()
    assert user.check_password(valid_new_password)


@pytest.mark.django_db
def test_dashboard(data_fixture, client):
    user, token = data_fixture.create_user_and_token(email="test@localhost")
    group_1 = data_fixture.create_group(name="Test1")
    group_2 = data_fixture.create_group()
    invitation_1 = data_fixture.create_group_invitation(
        group=group_1, email="test@localhost"
    )
    data_fixture.create_group_invitation(group=group_1, email="test2@localhost")
    data_fixture.create_group_invitation(group=group_2, email="test3@localhost")

    response = client.get(
        reverse("api:user:dashboard"), format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    response_json = response.json()
    assert len(response_json["group_invitations"]) == 1
    assert response_json["group_invitations"][0]["id"] == invitation_1.id
    assert response_json["group_invitations"][0]["email"] == invitation_1.email
    assert response_json["group_invitations"][0]["invited_by"] == (
        invitation_1.invited_by.first_name
    )
    assert response_json["group_invitations"][0]["group"] == "Test1"
    assert response_json["group_invitations"][0]["message"] == invitation_1.message
    assert "created_on" in response_json["group_invitations"][0]
