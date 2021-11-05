import os
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from itsdangerous.exc import BadSignature

from baserow.contrib.database.models import Database
from baserow.core.exceptions import (
    UserNotInGroup,
    ApplicationTypeDoesNotExist,
    ApplicationNotInGroup,
    GroupDoesNotExist,
    GroupUserDoesNotExist,
    GroupUserIsLastAdmin,
    ApplicationDoesNotExist,
    UserInvalidGroupPermissionsError,
    BaseURLHostnameNotAllowed,
    GroupInvitationEmailMismatch,
    GroupInvitationDoesNotExist,
    GroupUserAlreadyExists,
    IsNotAdminError,
    TemplateFileDoesNotExist,
    TemplateDoesNotExist,
)
from baserow.core.handler import CoreHandler
from baserow.core.models import (
    Settings,
    Group,
    GroupUser,
    GroupInvitation,
    Application,
    Template,
    TemplateCategory,
    GROUP_USER_PERMISSION_ADMIN,
)
from baserow.core.trash.handler import TrashHandler
from baserow.core.user_files.models import UserFile


@pytest.mark.django_db
def test_get_settings():
    settings = CoreHandler().get_settings()
    assert isinstance(settings, Settings)
    assert len(settings.instance_id) > 32
    assert settings.allow_new_signups is True


@pytest.mark.django_db
def test_update_settings(data_fixture):
    user_1 = data_fixture.create_user(is_staff=True)
    user_2 = data_fixture.create_user()

    with pytest.raises(IsNotAdminError):
        CoreHandler().update_settings(user_2, allow_new_signups=False)

    settings = CoreHandler().update_settings(
        user_1, allow_new_signups=False, instance_id="test"
    )
    assert settings.allow_new_signups is False
    assert settings.instance_id != "test"

    settings = Settings.objects.all().first()
    assert settings.instance_id != "test"
    assert settings.allow_new_signups is False


@pytest.mark.django_db
def test_get_group(data_fixture):
    user_1 = data_fixture.create_user()
    data_fixture.create_user()
    group_1 = data_fixture.create_group(user=user_1)

    handler = CoreHandler()

    with pytest.raises(GroupDoesNotExist):
        handler.get_group(group_id=0)

    group_1_copy = handler.get_group(group_id=group_1.id)
    assert group_1_copy.id == group_1.id

    # If the error is raised we know for sure that the query has resolved.
    with pytest.raises(AttributeError):
        handler.get_group(
            group_id=group_1.id, base_queryset=Group.objects.prefetch_related("UNKNOWN")
        )


@pytest.mark.django_db
def test_get_group_user(data_fixture):
    user_1 = data_fixture.create_user()
    data_fixture.create_user()
    group_1 = data_fixture.create_group()
    group_user_1 = data_fixture.create_user_group(user=user_1, group=group_1)

    handler = CoreHandler()

    with pytest.raises(GroupUserDoesNotExist):
        handler.get_group_user(group_user_id=0)

    group_user = handler.get_group_user(group_user_id=group_user_1.id)
    assert group_user.id == group_user_1.id
    assert group_user_1.group_id == group_1.id

    # If the error is raised we know for sure that the query has resolved.
    with pytest.raises(AttributeError):
        handler.get_group_user(
            group_user_id=group_user_1.id,
            base_queryset=GroupUser.objects.prefetch_related("UNKNOWN"),
        )


@pytest.mark.django_db
@patch("baserow.core.signals.group_user_updated.send")
def test_update_group_user(send_mock, data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    user_3 = data_fixture.create_user()
    group_1 = data_fixture.create_group()
    data_fixture.create_user_group(user=user_1, group=group_1, permissions="ADMIN")
    group_user_2 = data_fixture.create_user_group(
        user=user_2, group=group_1, permissions="MEMBER"
    )

    handler = CoreHandler()

    with pytest.raises(UserNotInGroup):
        handler.update_group_user(user=user_3, group_user=group_user_2)

    with pytest.raises(UserInvalidGroupPermissionsError):
        handler.update_group_user(user=user_2, group_user=group_user_2)

    tmp = handler.update_group_user(
        user=user_1, group_user=group_user_2, permissions="ADMIN"
    )

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["group_user"].id == group_user_2.id
    assert send_mock.call_args[1]["user"].id == user_1.id

    group_user_2.refresh_from_db()
    assert tmp.id == group_user_2.id
    assert tmp.permissions == "ADMIN"
    assert group_user_2.permissions == "ADMIN"


@pytest.mark.django_db
@patch("baserow.core.signals.group_user_deleted.send")
def test_delete_group_user(send_mock, data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    user_3 = data_fixture.create_user()
    group_1 = data_fixture.create_group()
    data_fixture.create_user_group(user=user_1, group=group_1, permissions="ADMIN")
    group_user_2 = data_fixture.create_user_group(
        user=user_2, group=group_1, permissions="MEMBER"
    )

    handler = CoreHandler()

    with pytest.raises(UserNotInGroup):
        handler.delete_group_user(user=user_3, group_user=group_user_2)

    with pytest.raises(UserInvalidGroupPermissionsError):
        handler.delete_group_user(user=user_2, group_user=group_user_2)

    group_user_id = group_user_2.id
    handler.delete_group_user(user=user_1, group_user=group_user_2)
    assert GroupUser.objects.all().count() == 1

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["group_user_id"] == group_user_id
    assert send_mock.call_args[1]["group_user"].group_id == group_user_2.group_id
    assert send_mock.call_args[1]["user"].id == user_1.id


@pytest.mark.django_db
@patch("baserow.core.signals.group_created.send")
def test_create_group(send_mock, data_fixture):
    user = data_fixture.create_user()

    handler = CoreHandler()
    group_user = handler.create_group(user=user, name="Test group")

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["group"].id == group_user.group.id
    assert send_mock.call_args[1]["user"].id == user.id

    group = Group.objects.all().first()
    user_group = GroupUser.objects.all().first()

    assert group.name == "Test group"
    assert user_group.user == user
    assert user_group.group == group
    assert user_group.order == 1
    assert user_group.permissions == GROUP_USER_PERMISSION_ADMIN

    handler.create_group(user=user, name="Test group 2")

    assert Group.objects.all().count() == 2
    assert GroupUser.objects.all().count() == 2


@pytest.mark.django_db
@patch("baserow.core.signals.group_restored.send")
def test_restore_group(group_restored_mock, data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(name="Test group", user=user)

    handler = CoreHandler()

    handler.delete_group(user, group)

    assert Group.objects.count() == 0

    TrashHandler.restore_item(user, "group", group.id)

    group_restored_mock.assert_called_once()
    assert group_restored_mock.call_args[1]["user"] is None
    assert (
        group_restored_mock.call_args[1]["group_user"].id
        == group.groupuser_set.get(user=user).id
    )

    group = Group.objects.all().first()
    user_group = GroupUser.objects.all().first()

    assert group.name == "Test group"
    assert user_group.user == user
    assert user_group.group == group
    assert user_group.permissions == GROUP_USER_PERMISSION_ADMIN


@pytest.mark.django_db
@patch("baserow.core.signals.group_updated.send")
def test_update_group(send_mock, data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user_1)

    handler = CoreHandler()
    handler.update_group(user=user_1, group=group, name="New name")

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["group"].id == group.id
    assert send_mock.call_args[1]["user"].id == user_1.id

    group.refresh_from_db()

    assert group.name == "New name"

    with pytest.raises(UserNotInGroup):
        handler.update_group(user=user_2, group=group, name="New name")

    with pytest.raises(ValueError):
        handler.update_group(user=user_2, group=object(), name="New name")


@pytest.mark.django_db
@patch("baserow.core.signals.group_user_deleted.send")
def test_leave_group(send_mock, data_fixture):
    user_1 = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    user_3 = data_fixture.create_user()
    user_4 = data_fixture.create_user()
    group_1 = data_fixture.create_group()
    group_2 = data_fixture.create_group()
    data_fixture.create_user_group(user=user_1, group=group_1, permissions="ADMIN")
    group_user_2 = data_fixture.create_user_group(
        user=user_2, group=group_1, permissions="ADMIN"
    )
    data_fixture.create_user_group(user=user_3, group=group_1, permissions="USER")
    data_fixture.create_user_group(user=user_3, group=group_2, permissions="USER")
    data_fixture.create_user_group(user=user_4, group=group_2, permissions="USER")

    handler = CoreHandler()

    with pytest.raises(UserNotInGroup):
        handler.leave_group(user=user_4, group=group_1)

    handler.leave_group(user=user_2, group=group_1)
    send_mock.assert_called_once()
    assert send_mock.call_args[1]["group_user_id"] == group_user_2.id
    assert send_mock.call_args[1]["group_user"].group_id == group_user_2.group_id
    assert send_mock.call_args[1]["user"].id == user_2.id

    with pytest.raises(GroupUserIsLastAdmin):
        handler.leave_group(user=user_1, group=group_1)

    handler.leave_group(user=user_3, group=group_1)

    assert GroupUser.objects.filter(user=user_1, group=group_1).exists() is True
    assert GroupUser.objects.filter(user=user_2, group=group_1).exists() is False
    assert GroupUser.objects.filter(user=user_3, group=group_1).exists() is False
    assert GroupUser.objects.filter(user=user_3, group=group_2).exists() is True
    assert GroupUser.objects.filter(user=user_4, group=group_2).exists() is True


@pytest.mark.django_db
@patch("baserow.core.signals.group_deleted.send")
def test_delete_group(send_mock, data_fixture):
    user = data_fixture.create_user()
    group_1 = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group_1)
    data_fixture.create_database_table(database=database)
    data_fixture.create_group(user=user)
    user_2 = data_fixture.create_user()
    group_3 = data_fixture.create_group(user=user_2)

    handler = CoreHandler()
    handler.delete_group(user, group_1)

    assert group_1.trashed

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["group"].id == group_1.id
    assert send_mock.call_args[1]["user"].id == user.id
    assert len(send_mock.call_args[1]["group_users"]) == 1
    assert send_mock.call_args[1]["group_users"][0].id == user.id

    assert Group.objects.count() == 2
    assert GroupUser.objects.count() == 2
    assert Group.trash.count() == 1
    assert GroupUser.trash.count() == 1

    with pytest.raises(UserNotInGroup):
        handler.delete_group(user, group_3)

    handler.delete_group(user_2, group_3)

    assert Group.objects.count() == 1
    assert GroupUser.objects.count() == 1
    assert Group.trash.count() == 2
    assert GroupUser.trash.count() == 2

    with pytest.raises(ValueError):
        handler.delete_group(user=user_2, group=object())


@pytest.mark.django_db
def test_order_groups(data_fixture):
    user = data_fixture.create_user()
    ug_1 = data_fixture.create_user_group(user=user, order=1)
    ug_2 = data_fixture.create_user_group(user=user, order=2)
    ug_3 = data_fixture.create_user_group(user=user, order=3)

    assert [1, 2, 3] == [ug_1.order, ug_2.order, ug_3.order]

    handler = CoreHandler()
    handler.order_groups(user, [ug_3.group.id, ug_2.group.id, ug_1.group.id])

    ug_1.refresh_from_db()
    ug_2.refresh_from_db()
    ug_3.refresh_from_db()

    assert [1, 2, 3] == [ug_3.order, ug_2.order, ug_1.order]

    handler.order_groups(user, [ug_2.group.id, ug_1.group.id, ug_3.group.id])

    ug_1.refresh_from_db()
    ug_2.refresh_from_db()
    ug_3.refresh_from_db()

    assert [1, 2, 3] == [ug_2.order, ug_1.order, ug_3.order]


@pytest.mark.django_db
def test_get_group_invitation_by_token(data_fixture):
    user = data_fixture.create_user()
    group_user = data_fixture.create_user_group(user=user)
    invitation = data_fixture.create_group_invitation(
        group=group_user.group, email=user.email
    )

    handler = CoreHandler()
    signer = handler.get_group_invitation_signer()

    with pytest.raises(BadSignature):
        handler.get_group_invitation_by_token(token="INVALID")

    with pytest.raises(GroupInvitationDoesNotExist):
        handler.get_group_invitation_by_token(token=signer.dumps(999999))

    invitation2 = handler.get_group_invitation_by_token(
        token=signer.dumps(invitation.id)
    )

    assert invitation.id == invitation2.id
    assert invitation.invited_by_id == invitation2.invited_by_id
    assert invitation.group_id == invitation2.group_id
    assert invitation.email == invitation2.email
    assert invitation.permissions == invitation2.permissions
    assert isinstance(invitation2, GroupInvitation)

    with pytest.raises(AttributeError):
        handler.get_group_invitation_by_token(
            token=signer.dumps(invitation.id),
            base_queryset=GroupInvitation.objects.prefetch_related("UNKNOWN"),
        )


@pytest.mark.django_db
def test_get_group_invitation(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    data_fixture.create_user()
    group_user = data_fixture.create_user_group(user=user)
    data_fixture.create_user_group(
        user=user_2, group=group_user.group, permissions="MEMBER"
    )
    invitation = data_fixture.create_group_invitation(
        group=group_user.group, email=user.email
    )

    handler = CoreHandler()

    with pytest.raises(GroupInvitationDoesNotExist):
        handler.get_group_invitation(group_invitation_id=999999)

    invitation2 = handler.get_group_invitation(group_invitation_id=invitation.id)

    assert invitation.id == invitation2.id
    assert invitation.invited_by_id == invitation2.invited_by_id
    assert invitation.group_id == invitation2.group_id
    assert invitation.email == invitation2.email
    assert invitation.permissions == invitation2.permissions
    assert isinstance(invitation2, GroupInvitation)

    with pytest.raises(AttributeError):
        handler.get_field(
            invitation_id=invitation.id,
            base_queryset=GroupInvitation.objects.prefetch_related("UNKNOWN"),
        )


@pytest.mark.django_db(transaction=True)
def test_send_group_invitation_email(data_fixture, mailoutbox):
    group_invitation = data_fixture.create_group_invitation()
    handler = CoreHandler()

    with pytest.raises(BaseURLHostnameNotAllowed):
        handler.send_group_invitation_email(
            invitation=group_invitation, base_url="http://test.nl/group-invite"
        )

    signer = handler.get_group_invitation_signer()
    handler.send_group_invitation_email(
        invitation=group_invitation, base_url="http://localhost:3000/group-invite"
    )

    assert len(mailoutbox) == 1
    email = mailoutbox[0]

    assert (
        email.subject == f"{group_invitation.invited_by.first_name} invited you "
        f"to {group_invitation.group.name} - Baserow"
    )
    assert email.from_email == "no-reply@localhost"
    assert group_invitation.email in email.to

    html_body = email.alternatives[0][0]
    search_url = "http://localhost:3000/group-invite/"
    start_url_index = html_body.index(search_url)

    assert start_url_index != -1

    end_url_index = html_body.index('"', start_url_index)
    token = html_body[start_url_index + len(search_url) : end_url_index]

    invitation_id = signer.loads(token)
    assert invitation_id == group_invitation.id


@pytest.mark.django_db(transaction=True)
def test_send_group_invitation_email_in_different_language(data_fixture, mailoutbox):
    user = data_fixture.create_user(language="fr")
    group_invitation = data_fixture.create_group_invitation(invited_by=user)

    handler = CoreHandler()
    handler.send_group_invitation_email(
        invitation=group_invitation, base_url="http://localhost:3000/group-invite"
    )

    assert len(mailoutbox) == 1
    assert (
        mailoutbox[0].subject
        == f"{group_invitation.invited_by.first_name} vous a invité à "
        f"{group_invitation.group.name} - Baserow"
    )


@pytest.mark.django_db
@patch("baserow.core.handler.CoreHandler.send_group_invitation_email")
def test_create_group_invitation(mock_send_email, data_fixture):
    user_group = data_fixture.create_user_group()
    user = user_group.user
    group = user_group.group
    user_2 = data_fixture.create_user()
    user_group_3 = data_fixture.create_user_group(group=group, permissions="MEMBER")
    user_3 = user_group_3.user

    handler = CoreHandler()

    with pytest.raises(UserNotInGroup):
        handler.create_group_invitation(
            user=user_2,
            group=group,
            email="test@test.nl",
            permissions="ADMIN",
            message="Test",
            base_url="http://localhost:3000/invite",
        )

    with pytest.raises(UserInvalidGroupPermissionsError):
        handler.create_group_invitation(
            user=user_3,
            group=group,
            email="test@test.nl",
            permissions="ADMIN",
            message="Test",
            base_url="http://localhost:3000/invite",
        )

    with pytest.raises(GroupUserAlreadyExists):
        handler.create_group_invitation(
            user=user,
            group=group,
            email=user_3.email,
            permissions="ADMIN",
            message="Test",
            base_url="http://localhost:3000/invite",
        )

    with pytest.raises(ValueError):
        handler.create_group_invitation(
            user=user,
            group=group,
            email="test@test.nl",
            permissions="NOT_EXISTING",
            message="Test",
            base_url="http://localhost:3000/invite",
        )

    invitation = handler.create_group_invitation(
        user=user,
        group=group,
        email="test@test.nl",
        permissions="ADMIN",
        message="Test",
        base_url="http://localhost:3000/invite",
    )
    assert invitation.invited_by_id == user.id
    assert invitation.group_id == group.id
    assert invitation.email == "test@test.nl"
    assert invitation.permissions == "ADMIN"
    assert invitation.message == "Test"
    assert GroupInvitation.objects.all().count() == 1

    mock_send_email.assert_called_once()
    assert mock_send_email.call_args[0][0].id == invitation.id
    assert mock_send_email.call_args[0][1] == "http://localhost:3000/invite"

    # Because there already is an invitation for this email and group, it must be
    # updated instead of having duplicates.
    invitation = handler.create_group_invitation(
        user=user,
        group=group,
        email="test@test.nl",
        permissions="MEMBER",
        message="New message",
        base_url="http://localhost:3000/invite",
    )
    assert invitation.invited_by_id == user.id
    assert invitation.group_id == group.id
    assert invitation.email == "test@test.nl"
    assert invitation.permissions == "MEMBER"
    assert invitation.message == "New message"
    assert GroupInvitation.objects.all().count() == 1

    invitation = handler.create_group_invitation(
        user=user,
        group=group,
        email="test2@test.nl",
        permissions="ADMIN",
        message="",
        base_url="http://localhost:3000/invite",
    )
    assert invitation.invited_by_id == user.id
    assert invitation.group_id == group.id
    assert invitation.email == "test2@test.nl"
    assert invitation.permissions == "ADMIN"
    assert invitation.message == ""
    assert GroupInvitation.objects.all().count() == 2

    invitation = handler.create_group_invitation(
        user=user,
        group=group,
        email="test3@test.nl",
        permissions="ADMIN",
        base_url="http://localhost:3000/invite",
    )
    assert invitation.invited_by_id == user.id
    assert invitation.group_id == group.id
    assert invitation.email == "test3@test.nl"
    assert invitation.permissions == "ADMIN"
    assert invitation.message == ""
    assert GroupInvitation.objects.all().count() == 3


@pytest.mark.django_db
def test_update_group_invitation(data_fixture):
    group_invitation = data_fixture.create_group_invitation()
    user = group_invitation.invited_by
    user_2 = data_fixture.create_user()
    handler = CoreHandler()

    with pytest.raises(UserNotInGroup):
        handler.update_group_invitation(
            user=user_2, invitation=group_invitation, permissions="ADMIN"
        )

    with pytest.raises(ValueError):
        handler.update_group_invitation(
            user=user, invitation=group_invitation, permissions="NOT_EXISTING"
        )

    invitation = handler.update_group_invitation(
        user=user, invitation=group_invitation, permissions="MEMBER"
    )

    assert invitation.permissions == "MEMBER"
    invitation = GroupInvitation.objects.all().first()
    assert invitation.permissions == "MEMBER"


@pytest.mark.django_db
def test_delete_group_invitation(data_fixture):
    group_invitation = data_fixture.create_group_invitation()
    user = group_invitation.invited_by
    user_2 = data_fixture.create_user()
    handler = CoreHandler()

    with pytest.raises(UserNotInGroup):
        handler.delete_group_invitation(
            user=user_2,
            invitation=group_invitation,
        )

    handler.delete_group_invitation(
        user=user,
        invitation=group_invitation,
    )
    assert GroupInvitation.objects.all().count() == 0


@pytest.mark.django_db
def test_reject_group_invitation(data_fixture):
    group_invitation = data_fixture.create_group_invitation(email="test@test.nl")
    user_1 = data_fixture.create_user(email="test@test.nl")
    user_2 = data_fixture.create_user(email="test2@test.nl")

    handler = CoreHandler()

    with pytest.raises(GroupInvitationEmailMismatch):
        handler.reject_group_invitation(user=user_2, invitation=group_invitation)

    assert GroupInvitation.objects.all().count() == 1

    handler.reject_group_invitation(user=user_1, invitation=group_invitation)
    assert GroupInvitation.objects.all().count() == 0
    assert GroupUser.objects.all().count() == 1


@pytest.mark.django_db
def test_accept_group_invitation(data_fixture):
    group = data_fixture.create_group()
    group_2 = data_fixture.create_group()
    group_invitation = data_fixture.create_group_invitation(
        email="test@test.nl", permissions="MEMBER", group=group
    )
    user_1 = data_fixture.create_user(email="test@test.nl")
    user_2 = data_fixture.create_user(email="test2@test.nl")

    handler = CoreHandler()

    with pytest.raises(GroupInvitationEmailMismatch):
        handler.accept_group_invitation(user=user_2, invitation=group_invitation)

    assert GroupInvitation.objects.all().count() == 1

    group_user = handler.accept_group_invitation(
        user=user_1, invitation=group_invitation
    )
    assert group_user.group_id == group.id
    assert group_user.permissions == "MEMBER"
    assert GroupInvitation.objects.all().count() == 0
    assert GroupUser.objects.all().count() == 1

    group_invitation = data_fixture.create_group_invitation(
        email="test@test.nl", permissions="ADMIN", group=group
    )
    group_user = handler.accept_group_invitation(
        user=user_1, invitation=group_invitation
    )
    assert group_user.group_id == group.id
    assert group_user.permissions == "ADMIN"
    assert GroupInvitation.objects.all().count() == 0
    assert GroupUser.objects.all().count() == 1

    group_invitation = data_fixture.create_group_invitation(
        email="test@test.nl", permissions="MEMBER", group=group_2
    )
    group_user = handler.accept_group_invitation(
        user=user_1, invitation=group_invitation
    )
    assert group_user.group_id == group_2.id
    assert group_user.permissions == "MEMBER"
    assert GroupInvitation.objects.all().count() == 0
    assert GroupUser.objects.all().count() == 2


@pytest.mark.django_db
def test_get_application(data_fixture):
    user_1 = data_fixture.create_user()
    data_fixture.create_user()
    application_1 = data_fixture.create_database_application(user=user_1)

    handler = CoreHandler()

    with pytest.raises(ApplicationDoesNotExist):
        handler.get_application(application_id=0)

    application_1_copy = handler.get_application(application_id=application_1.id)
    assert application_1_copy.id == application_1.id
    assert isinstance(application_1_copy, Application)

    database_1_copy = handler.get_application(
        application_id=application_1.id, base_queryset=Database.objects
    )
    assert database_1_copy.id == application_1.id
    assert isinstance(database_1_copy, Database)


@pytest.mark.django_db
@patch("baserow.core.signals.application_created.send")
def test_create_database_application(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)

    handler = CoreHandler()
    handler.create_application(
        user=user, group=group, type_name="database", name="Test database"
    )

    assert Application.objects.all().count() == 1
    assert Database.objects.all().count() == 1

    database = Database.objects.all().first()
    assert database.name == "Test database"
    assert database.order == 1
    assert database.group == group

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["application"].id == database.id
    assert send_mock.call_args[1]["user"].id == user.id

    with pytest.raises(UserNotInGroup):
        handler.create_application(
            user=user_2, group=group, type_name="database", name=""
        )

    with pytest.raises(ApplicationTypeDoesNotExist):
        handler.create_application(user=user, group=group, type_name="UNKNOWN", name="")


@pytest.mark.django_db
@patch("baserow.core.signals.application_updated.send")
def test_update_database_application(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)

    handler = CoreHandler()

    with pytest.raises(UserNotInGroup):
        handler.update_application(user=user_2, application=database, name="Test 1")

    with pytest.raises(ValueError):
        handler.update_application(user=user_2, application=object(), name="Test 1")

    handler.update_application(user=user, application=database, name="Test 1")

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["application"].id == database.id
    assert send_mock.call_args[1]["user"].id == user.id

    database.refresh_from_db()

    assert database.name == "Test 1"


@pytest.mark.django_db
@patch("baserow.core.signals.applications_reordered.send")
def test_order_applications(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    application_1 = data_fixture.create_database_application(group=group, order=1)
    application_2 = data_fixture.create_database_application(group=group, order=2)
    application_3 = data_fixture.create_database_application(group=group, order=3)

    handler = CoreHandler()

    with pytest.raises(UserNotInGroup):
        handler.order_applications(user=user_2, group=group, order=[])

    with pytest.raises(ApplicationNotInGroup):
        handler.order_applications(user=user, group=group, order=[0])

    handler.order_applications(
        user=user,
        group=group,
        order=[application_3.id, application_2.id, application_1.id],
    )
    application_1.refresh_from_db()
    application_2.refresh_from_db()
    application_3.refresh_from_db()
    assert application_1.order == 3
    assert application_2.order == 2
    assert application_3.order == 1

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["group"].id == group.id
    assert send_mock.call_args[1]["user"].id == user.id
    assert send_mock.call_args[1]["order"] == [
        application_3.id,
        application_2.id,
        application_1.id,
    ]

    handler.order_applications(
        user=user,
        group=group,
        order=[application_1.id, application_3.id, application_2.id],
    )
    application_1.refresh_from_db()
    application_2.refresh_from_db()
    application_3.refresh_from_db()
    assert application_1.order == 1
    assert application_2.order == 3
    assert application_3.order == 2

    handler.order_applications(user=user, group=group, order=[application_1.id])
    application_1.refresh_from_db()
    application_2.refresh_from_db()
    application_3.refresh_from_db()
    assert application_1.order == 1
    assert application_2.order == 0
    assert application_3.order == 0


@pytest.mark.django_db
@patch("baserow.core.signals.application_deleted.send")
def test_delete_database_application(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(group=group)
    data_fixture.create_database_table(database=database)

    handler = CoreHandler()

    with pytest.raises(UserNotInGroup):
        handler.delete_application(user=user_2, application=database)

    with pytest.raises(ValueError):
        handler.delete_application(user=user_2, application=object())

    handler.delete_application(user=user, application=database)

    database.refresh_from_db()
    assert database.trashed

    assert Database.objects.all().count() == 0
    assert Database.trash.all().count() == 1

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["application_id"] == database.id
    assert send_mock.call_args[1]["application"].id == database.id
    assert send_mock.call_args[1]["user"].id == user.id


@pytest.mark.django_db
def test_get_template(data_fixture):
    data_fixture.create_user()
    template_1 = data_fixture.create_template()

    handler = CoreHandler()

    with pytest.raises(TemplateDoesNotExist):
        handler.get_template(template_id=0)

    template_1_copy = handler.get_template(template_id=template_1.id)
    assert template_1_copy.id == template_1.id

    # If the error is raised we know for sure that the query has resolved.
    with pytest.raises(AttributeError):
        handler.get_template(
            template_id=template_1.id,
            base_queryset=Template.objects.prefetch_related("UNKNOWN"),
        )


@pytest.mark.django_db
def test_export_import_group_application(data_fixture):
    group = data_fixture.create_group()
    imported_group = data_fixture.create_group()
    database = data_fixture.create_database_application(group=group)
    data_fixture.create_database_table(database=database)

    handler = CoreHandler()
    exported_applications = handler.export_group_applications(group, BytesIO())
    imported_applications, id_mapping = handler.import_applications_to_group(
        imported_group, exported_applications, BytesIO(), None
    )

    assert len(imported_applications) == 1
    imported_database = imported_applications[0]
    assert imported_database.id != database.id
    assert imported_database.name == database.name
    assert imported_database.order == database.order
    assert imported_database.table_set.all().count() == 1
    assert database.id in id_mapping["applications"]
    assert id_mapping["applications"][database.id] == imported_database.id


@pytest.mark.django_db
def test_sync_all_templates():
    handler = CoreHandler()
    handler.sync_templates()

    assert Template.objects.count() == len(
        list(Path(settings.APPLICATION_TEMPLATES_DIR).glob("*.json"))
    )


@pytest.mark.django_db
def test_sync_templates(data_fixture, tmpdir):
    old_templates = settings.APPLICATION_TEMPLATES_DIR
    settings.APPLICATION_TEMPLATES_DIR = os.path.join(
        settings.BASE_DIR, "../../../tests/templates"
    )

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")

    group_1 = data_fixture.create_group()
    group_2 = data_fixture.create_group()
    group_3 = data_fixture.create_group()

    category_1 = data_fixture.create_template_category(name="No templates")
    category_2 = data_fixture.create_template_category(name="Has template")
    template = data_fixture.create_template(
        slug="is-going-to-be-deleted", group=group_1, category=category_2
    )
    template_2 = data_fixture.create_template(
        slug="example-template",
        group=group_2,
        category=category_2,
        export_hash="IS_NOT_GOING_MATCH",
    )
    template_3 = data_fixture.create_template(
        slug="example-template-2",
        group=group_3,
        category=category_2,
        export_hash="f086c9b4b0dfea6956d0bb32af210277bb645ff3faebc5fb37a9eae85c433f2d",
    )

    handler = CoreHandler()
    handler.sync_templates(storage=storage)

    groups = Group.objects.all().order_by("id")
    assert len(groups) == 3
    assert groups[0].id == group_3.id
    assert groups[1].id not in [group_1.id, group_2.id]
    assert groups[2].id not in [group_1.id, group_2.id]

    assert not TemplateCategory.objects.filter(id=category_1.id).exists()
    assert not TemplateCategory.objects.filter(id=category_2.id).exists()
    categories = TemplateCategory.objects.all()
    assert len(categories) == 1
    assert categories[0].name == "Test category 1"

    assert not Template.objects.filter(id=template.id).exists()
    assert Template.objects.filter(id=template_2.id).exists()
    assert Template.objects.filter(id=template_3.id).exists()

    refreshed_template_2 = Template.objects.get(id=template_2.id)
    assert refreshed_template_2.name == "Example template"
    assert refreshed_template_2.icon == "file"
    assert (
        refreshed_template_2.export_hash
        == "7d86876e8fa061bb0deec179ce2a1b24a220f5cd4eb6ddacbdccf036160c7bf3"
    )
    assert refreshed_template_2.keywords == "Example,Template,For,Search"
    assert refreshed_template_2.categories.all().first().id == categories[0].id
    assert template_2.group_id != refreshed_template_2.group_id
    assert refreshed_template_2.group.name == "Example template"
    assert refreshed_template_2.group.application_set.count() == 1

    refreshed_template_3 = Template.objects.get(id=template_3.id)
    assert template_3.group_id == refreshed_template_3.group_id
    # We expect the group count to be zero because the export hash matches and
    # nothing was updated.
    assert refreshed_template_3.group.application_set.count() == 0

    # Because the `example-template.json` has a file field that contains the hello
    # world file, we expect it to exist after syncing the templates.
    assert UserFile.objects.all().count() == 1
    user_file = UserFile.objects.all().first()
    assert user_file.original_name == "hello.txt"
    file_path = tmpdir.join("user_files", user_file.name)
    assert file_path.isfile()
    assert file_path.open().read() == "Hello World"

    settings.APPLICATION_TEMPLATES_DIR = old_templates


@pytest.mark.django_db
@patch("baserow.core.signals.application_created.send")
def test_install_template(send_mock, tmpdir, data_fixture):
    old_templates = settings.APPLICATION_TEMPLATES_DIR
    settings.APPLICATION_TEMPLATES_DIR = os.path.join(
        settings.BASE_DIR, "../../../tests/templates"
    )

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")

    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    group_2 = data_fixture.create_group()

    handler = CoreHandler()
    handler.sync_templates(storage=storage)

    template_2 = data_fixture.create_template(slug="does-not-exist")

    with pytest.raises(TemplateFileDoesNotExist):
        handler.install_template(user, group, template_2, storage=storage)

    template = Template.objects.get(slug="example-template")

    with pytest.raises(UserNotInGroup):
        handler.install_template(user, group_2, template, storage=storage)

    applications, id_mapping = handler.install_template(
        user, group, template, storage=storage
    )
    assert len(applications) == 1
    assert applications[0].group_id == group.id
    assert applications[0].name == "Event marketing"

    send_mock.assert_called_once()
    assert send_mock.call_args[1]["application"].id == applications[0].id
    assert send_mock.call_args[1]["user"].id == user.id

    # Because the `example-template.json` has a file field that contains the hello
    # world file, we expect it to exist after syncing the templates.
    assert UserFile.objects.all().count() == 1
    user_file = UserFile.objects.all().first()
    assert user_file.original_name == "hello.txt"
    file_path = tmpdir.join("user_files", user_file.name)
    assert file_path.isfile()
    assert file_path.open().read() == "Hello World"

    settings.APPLICATION_TEMPLATES_DIR = old_templates


@pytest.mark.django_db
@patch("baserow.core.signals.application_created.send")
def test_restore_application(application_created_mock, data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(name="Test group", user=user)
    database = data_fixture.create_database_application(user=user, group=group)

    handler = CoreHandler()

    handler.delete_application(user, application=database)

    assert Application.objects.count() == 0

    TrashHandler.restore_item(user, "application", database.id)

    application_created_mock.assert_called_once()
    assert application_created_mock.call_args[1]["application"].id == database.id
    assert application_created_mock.call_args[1]["user"] is None

    restored_app = Application.objects.all().first()

    assert restored_app.name == database.name
    assert restored_app.id == database.id
