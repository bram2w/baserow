from django.contrib.auth.models import AnonymousUser
from django.test.utils import override_settings

import pytest
from rest_framework.exceptions import NotAuthenticated

from baserow.core.exceptions import (
    PermissionDenied,
    UserInvalidGroupPermissionsError,
    UserNotInGroup,
)
from baserow.core.handler import CoreHandler
from baserow.core.operations import (
    ListApplicationsGroupOperationType,
    UpdateGroupOperationType,
)
from baserow.core.registries import permission_manager_type_registry


@pytest.mark.django_db
@override_settings(PERMISSION_MANAGERS=["core", "staff", "member", "basic"])
def test_group_check_basic_permissions(data_fixture):
    user = data_fixture.create_user()
    user_group = data_fixture.create_user_group(permissions="ADMIN")
    user_group_2 = data_fixture.create_user_group(permissions="MEMBER")
    user_group_3 = data_fixture.create_user_group()
    data_fixture.create_template(group=user_group_3.group)

    # An external user shouldn't be allowed
    with pytest.raises(UserNotInGroup):
        CoreHandler().check_permissions(
            user,
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
        )

    with pytest.raises(UserNotInGroup):
        CoreHandler().check_permissions(
            user,
            UpdateGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
        )

    assert (
        CoreHandler().check_permissions(
            user,
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
            raise_error=False,
        )
        is False
    )

    assert CoreHandler().check_permissions(
        user_group.user,
        ListApplicationsGroupOperationType.type,
        group=user_group.group,
        context=user_group.group,
    )
    assert CoreHandler().check_permissions(
        user_group.user,
        UpdateGroupOperationType.type,
        group=user_group.group,
        context=user_group.group,
    )

    assert CoreHandler().check_permissions(
        user_group_2.user,
        ListApplicationsGroupOperationType.type,
        group=user_group_2.group,
        context=user_group.group,
    )

    with pytest.raises(UserInvalidGroupPermissionsError):
        assert CoreHandler().check_permissions(
            user_group_2.user,
            UpdateGroupOperationType.type,
            group=user_group_2.group,
            context=user_group_2.group,
        )

    with pytest.raises(NotAuthenticated):
        assert CoreHandler().check_permissions(
            AnonymousUser(),
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
        )

    basic_permission_manager = permission_manager_type_registry.get("basic")
    original_check = basic_permission_manager.check_permissions
    basic_permission_manager.check_permissions = lambda *args, **kwargs: None

    with pytest.raises(PermissionDenied):
        CoreHandler().check_permissions(
            user_group.user,
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            context=user_group.group,
        )

    basic_permission_manager.check_permissions = original_check

    with pytest.raises(UserInvalidGroupPermissionsError):
        assert CoreHandler().check_permissions(
            user_group_2.user,
            UpdateGroupOperationType.type,
            group=user_group_2.group,
            context=user_group_2.group,
            allow_if_template=True,
        )

    assert CoreHandler().check_permissions(
        user_group_3.user,
        UpdateGroupOperationType.type,
        group=user_group_3.group,
        context=user_group_3.group,
        allow_if_template=True,
    )

    with pytest.raises(NotAuthenticated):
        assert CoreHandler().check_permissions(
            AnonymousUser(),
            ListApplicationsGroupOperationType.type,
            group=user_group.group,
            allow_if_template=True,
            context=user_group.group,
        )
