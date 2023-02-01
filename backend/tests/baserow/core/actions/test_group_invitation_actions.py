import pytest

from baserow.core.action.registries import action_type_registry
from baserow.core.actions import (
    AcceptGroupInvitationActionType,
    CreateGroupInvitationActionType,
    DeleteGroupInvitationActionType,
    RejectGroupInvitationActionType,
    UpdateGroupInvitationActionType,
)
from baserow.core.models import GroupInvitation


@pytest.mark.django_db
def test_create_group_invitation_action_type(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    invitation = action_type_registry.get(CreateGroupInvitationActionType.type).do(
        user=user,
        group=group,
        email="user@test.com",
        permissions="ADMIN",
        base_url="http://localhost:3000/",
        message="hello!",
    )

    assert invitation.group == group
    assert invitation.email == "user@test.com"
    assert invitation.permissions == "ADMIN"
    assert invitation.invited_by == user


@pytest.mark.django_db
def test_update_group_invitation_action_type(data_fixture):
    user = data_fixture.create_user()
    invitation = data_fixture.create_group_invitation(invited_by=user)

    assert invitation.permissions == "ADMIN"
    action_type_registry.get(UpdateGroupInvitationActionType.type).do(
        user, invitation, permissions="MEMBER"
    )
    assert invitation.permissions == "MEMBER"


@pytest.mark.django_db
def test_delete_group_invitation_action_type(data_fixture):

    user = data_fixture.create_user()
    invitation = data_fixture.create_group_invitation(invited_by=user)

    assert GroupInvitation.objects.count() == 1
    action_type_registry.get(DeleteGroupInvitationActionType.type).do(user, invitation)
    assert GroupInvitation.objects.count() == 0


@pytest.mark.django_db
def test_accept_group_invitation_action_type(data_fixture):
    sender = data_fixture.create_user()
    group = data_fixture.create_group(user=sender)
    user = data_fixture.create_user()
    invitation = data_fixture.create_group_invitation(
        invited_by=sender, group=group, email=user.email
    )

    action_type_registry.get(AcceptGroupInvitationActionType.type).do(user, invitation)
    assert group.users.filter(id=user.id).exists()


@pytest.mark.django_db
def test_reject_group_invitation_action_type(data_fixture):
    sender = data_fixture.create_user()
    group = data_fixture.create_group(user=sender)
    user = data_fixture.create_user()
    invitation = data_fixture.create_group_invitation(
        invited_by=sender, group=group, email=user.email
    )

    action_type_registry.get(RejectGroupInvitationActionType.type).do(user, invitation)
    assert group.users.filter(id=user.id).exists() is False
