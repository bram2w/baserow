import pytest
from freezegun import freeze_time

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from django.shortcuts import reverse

from baserow.core.handler import CoreHandler
from baserow.core.models import GroupUser, GroupInvitation


@pytest.mark.django_db
def test_list_group_invitations(api_client, data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    group_1 = data_fixture.create_group(user=user_1)
    group_2 = data_fixture.create_group()
    data_fixture.create_user_group(group=group_1, user=user_2, permissions="MEMBER")
    with freeze_time("2020-01-02 12:00"):
        invitation_1 = data_fixture.create_group_invitation(
            group=group_1,
            invited_by=user_1,
            email="test3@test.nl",
            permissions="MEMBER",
            message="Test bericht 1",
        )
    invitation_2 = data_fixture.create_group_invitation(
        group=group_1,
        invited_by=user_1,
        email="test4@test.nl",
        permissions="ADMIN",
        message="Test bericht 2",
    )

    response = api_client.get(
        reverse("api:groups:invitations:list", kwargs={"group_id": 999999}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"

    response = api_client.get(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_2.id}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_1.id}),
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_INVALID_GROUP_PERMISSIONS"
    assert response.json()["detail"] == "You need ['ADMIN'] permissions."

    response = api_client.get(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_1.id}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 2
    assert response_json[0]["id"] == invitation_1.id
    assert response_json[0]["group"] == invitation_1.group_id
    assert response_json[0]["email"] == "test3@test.nl"
    assert response_json[0]["permissions"] == "MEMBER"
    assert response_json[0]["message"] == "Test bericht 1"
    assert response_json[0]["created_on"] == "2020-01-02T12:00:00Z"
    assert response_json[1]["id"] == invitation_2.id


@pytest.mark.django_db
def test_create_group_invitation(api_client, data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    user_3, token_3 = data_fixture.create_user_and_token(email="test3@test.nl")
    group_1 = data_fixture.create_group(user=user_1)
    data_fixture.create_user_group(group=group_1, user=user_3, permissions="MEMBER")

    response = api_client.post(
        reverse("api:groups:invitations:list", kwargs={"group_id": 99999}),
        {
            "email": "test@test.nl",
            "permissions": "ADMIN",
            "message": "Test",
            "base_url": "http://localhost:3000/invite",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_GROUP_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_1.id}),
        {
            "email": "test@test.nl",
            "permissions": "ADMIN",
            "message": "Test",
            "base_url": "http://localhost:3000/invite",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.post(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_1.id}),
        {
            "email": user_3.email,
            "permissions": "ADMIN",
            "message": "Test",
            "base_url": "http://localhost:3000/invite",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_GROUP_USER_ALREADY_EXISTS"

    response = api_client.post(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_1.id}),
        {
            "email": "test@test.nl",
            "permissions": "ADMIN",
            "message": "Test",
            "base_url": "http://localhost:3000/invite",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_3}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_INVALID_GROUP_PERMISSIONS"

    response = api_client.post(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_1.id}),
        {
            "email": "NO_EMAIL",
            "permissions": "NOT_EXISTING",
            "message": "",
            "base_url": "http://localhost:3000/invite",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["email"][0]["code"] == "invalid"
    assert response_json["detail"]["permissions"][0]["code"] == "invalid_choice"
    assert "message" not in response_json["detail"]

    response = api_client.post(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_1.id}),
        {
            "email": "test@test.nl",
            "permissions": "ADMIN",
            "message": "Test",
            "base_url": "http://test.nl:3000/invite",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_HOSTNAME_IS_NOT_ALLOWED"

    response = api_client.post(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_1.id}),
        {
            "email": "test0@test.nl",
            "permissions": "ADMIN",
            "message": "Test",
            "base_url": "http://localhost:3000/invite",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    invitation = GroupInvitation.objects.all().first()
    assert response_json["id"] == invitation.id
    assert response_json["group"] == invitation.group_id
    assert response_json["email"] == "test0@test.nl"
    assert response_json["permissions"] == "ADMIN"
    assert response_json["message"] == "Test"
    assert "created_on" in response_json

    response = api_client.post(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_1.id}),
        {
            "email": "test2@test.nl",
            "permissions": "ADMIN",
            "message": "",
            "base_url": "http://localhost:3000/invite",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["message"] == ""

    response = api_client.post(
        reverse("api:groups:invitations:list", kwargs={"group_id": group_1.id}),
        {
            "email": "test2@test.nl",
            "permissions": "ADMIN",
            "base_url": "http://localhost:3000/invite",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["message"] == ""


@pytest.mark.django_db
def test_get_group_invitation(api_client, data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    user_3, token_3 = data_fixture.create_user_and_token(email="test3@test.nl")
    group_1 = data_fixture.create_group()
    data_fixture.create_user_group(group=group_1, user=user_1, permissions="ADMIN")
    data_fixture.create_user_group(group=group_1, user=user_2, permissions="MEMBER")
    invitation = data_fixture.create_group_invitation(
        invited_by=user_1,
        group=group_1,
        email="test0@test.nl",
        permissions="ADMIN",
        message="TEst",
    )

    response = api_client.get(
        reverse("api:groups:invitations:item", kwargs={"group_invitation_id": 99999}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_GROUP_INVITATION_DOES_NOT_EXIST"

    response = api_client.get(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token_3}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_INVALID_GROUP_PERMISSIONS"

    response = api_client.get(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == invitation.id
    assert response_json["group"] == invitation.group_id
    assert response_json["email"] == invitation.email
    assert response_json["permissions"] == invitation.permissions
    assert response_json["message"] == invitation.message
    assert "created_on" in response_json


@pytest.mark.django_db
def test_update_group_invitation(api_client, data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    user_3, token_3 = data_fixture.create_user_and_token(email="test3@test.nl")
    group_1 = data_fixture.create_group()
    data_fixture.create_user_group(group=group_1, user=user_1, permissions="ADMIN")
    data_fixture.create_user_group(group=group_1, user=user_2, permissions="MEMBER")
    invitation = data_fixture.create_group_invitation(
        invited_by=user_1,
        group=group_1,
        email="test0@test.nl",
        permissions="ADMIN",
        message="TEst",
    )

    response = api_client.patch(
        reverse("api:groups:invitations:item", kwargs={"group_invitation_id": 99999}),
        {"permissions": "MEMBER"},
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_GROUP_INVITATION_DOES_NOT_EXIST"

    response = api_client.patch(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        {"permissions": "MEMBER"},
        HTTP_AUTHORIZATION=f"JWT {token_3}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.patch(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        {"permissions": "MEMBER"},
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_INVALID_GROUP_PERMISSIONS"

    response = api_client.patch(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        {"permissions": "NOT_EXISTING"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["permissions"][0]["code"] == "invalid_choice"

    response = api_client.patch(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        {"permissions": "MEMBER"},
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == invitation.id
    assert response_json["group"] == invitation.group_id
    assert response_json["email"] == invitation.email
    assert response_json["permissions"] == "MEMBER"
    assert response_json["message"] == invitation.message
    assert "created_on" in response_json

    response = api_client.patch(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        {
            "email": "should.be@ignored.nl",
            "permissions": "ADMIN",
            "message": "Should be ignored",
            "base_url": "http://should.be.ignored:3000/invite",
        },
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == invitation.id
    assert response_json["group"] == invitation.group_id
    assert response_json["email"] == invitation.email
    assert response_json["permissions"] == "ADMIN"
    assert response_json["message"] == invitation.message


@pytest.mark.django_db
def test_delete_group_invitation(api_client, data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    user_3, token_3 = data_fixture.create_user_and_token(email="test3@test.nl")
    group_1 = data_fixture.create_group()
    data_fixture.create_user_group(group=group_1, user=user_1, permissions="ADMIN")
    data_fixture.create_user_group(group=group_1, user=user_2, permissions="MEMBER")
    invitation = data_fixture.create_group_invitation(
        invited_by=user_1,
        group=group_1,
        email="test0@test.nl",
        permissions="ADMIN",
        message="TEst",
    )

    response = api_client.delete(
        reverse("api:groups:invitations:item", kwargs={"group_invitation_id": 99999}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_GROUP_INVITATION_DOES_NOT_EXIST"

    response = api_client.delete(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token_3}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.delete(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_INVALID_GROUP_PERMISSIONS"

    response = api_client.delete(
        reverse(
            "api:groups:invitations:item", kwargs={"group_invitation_id": invitation.id}
        ),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT
    assert GroupInvitation.objects.all().count() == 0


@pytest.mark.django_db
def test_accept_group_invitation(api_client, data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    group_1 = data_fixture.create_group()
    invitation = data_fixture.create_group_invitation(
        invited_by=user_1,
        group=group_1,
        email="test1@test.nl",
        permissions="ADMIN",
        message="Test",
    )

    response = api_client.post(
        reverse("api:groups:invitations:accept", kwargs={"group_invitation_id": 99999}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_GROUP_INVITATION_DOES_NOT_EXIST"

    response = api_client.post(
        reverse(
            "api:groups:invitations:accept",
            kwargs={"group_invitation_id": invitation.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_GROUP_INVITATION_EMAIL_MISMATCH"

    response = api_client.post(
        reverse(
            "api:groups:invitations:accept",
            kwargs={"group_invitation_id": invitation.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert "id" in response_json
    assert response_json["permissions"] == "ADMIN"
    assert response_json["name"] == group_1.name
    assert response_json["order"] == 1
    assert GroupInvitation.objects.all().count() == 0
    assert GroupUser.objects.all().count() == 1


@pytest.mark.django_db
def test_reject_group_invitation(api_client, data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    group_1 = data_fixture.create_group()
    invitation = data_fixture.create_group_invitation(
        invited_by=user_1,
        group=group_1,
        email="test1@test.nl",
        permissions="ADMIN",
        message="Test",
    )

    response = api_client.post(
        reverse("api:groups:invitations:reject", kwargs={"group_invitation_id": 99999}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_GROUP_INVITATION_DOES_NOT_EXIST"

    response = api_client.post(
        reverse(
            "api:groups:invitations:reject",
            kwargs={"group_invitation_id": invitation.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_GROUP_INVITATION_EMAIL_MISMATCH"

    response = api_client.post(
        reverse(
            "api:groups:invitations:reject",
            kwargs={"group_invitation_id": invitation.id},
        ),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT
    assert GroupInvitation.objects.all().count() == 0
    assert GroupUser.objects.all().count() == 0


@pytest.mark.django_db
def test_get_group_invitation_by_token(api_client, data_fixture):
    data_fixture.create_user(email="test1@test.nl")
    invitation = data_fixture.create_group_invitation(
        email="test0@test.nl", permissions="ADMIN", message="TEst"
    )
    invitation_2 = data_fixture.create_group_invitation(
        email="test1@test.nl",
        permissions="ADMIN",
    )

    handler = CoreHandler()
    signer = handler.get_group_invitation_signer()

    response = api_client.get(
        reverse("api:groups:invitations:token", kwargs={"token": "INVALID"}),
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "BAD_TOKEN_SIGNATURE"

    response = api_client.get(
        reverse("api:groups:invitations:token", kwargs={"token": signer.dumps(99999)}),
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_GROUP_INVITATION_DOES_NOT_EXIST"

    response = api_client.get(
        reverse(
            "api:groups:invitations:token",
            kwargs={"token": signer.dumps(invitation.id)},
        ),
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == invitation.id
    assert response_json["invited_by"] == invitation.invited_by.first_name
    assert response_json["group"] == invitation.group.name
    assert response_json["email"] == invitation.email
    assert response_json["message"] == invitation.message
    assert response_json["email_exists"] is False
    assert "created_on" in response_json

    response = api_client.get(
        reverse(
            "api:groups:invitations:token",
            kwargs={"token": signer.dumps(invitation_2.id)},
        ),
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["id"] == invitation_2.id
    assert response_json["email_exists"] is True
