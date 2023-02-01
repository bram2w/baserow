import pytest

from baserow.core.exceptions import PermissionException
from baserow.core.operations import CreateGroupOperationType
from baserow.core.permission_manager import (
    StaffOnlySettingOperationPermissionManagerType,
)


@pytest.mark.django_db
def test_staff_setting_permission_manager_staff_with_allow_global_group_creation_disabled(
    data_fixture,
):
    # With group creation disabled, staff can still create groups.
    perm_manager = StaffOnlySettingOperationPermissionManagerType()
    user = data_fixture.create_user(is_staff=True)
    data_fixture.update_settings(allow_global_group_creation=False)
    assert perm_manager.check_permissions(user, CreateGroupOperationType.type)
    assert perm_manager.get_permissions_object(user) == {
        "always_allowed_operations": [],
        "staff_only_operations": [CreateGroupOperationType.type],
    }


@pytest.mark.django_db
def test_staff_setting_permission_manager_staff_with_allow_global_group_creation_enabled(
    data_fixture,
):
    # With group creation enabled, staff can still create groups.
    perm_manager = StaffOnlySettingOperationPermissionManagerType()
    user = data_fixture.create_user(is_staff=True)
    data_fixture.update_settings(allow_global_group_creation=True)
    assert perm_manager.check_permissions(user, CreateGroupOperationType.type)
    assert perm_manager.get_permissions_object(user) == {
        "staff_only_operations": [],
        "always_allowed_operations": [CreateGroupOperationType.type],
    }


@pytest.mark.django_db
def test_staff_setting_permission_manager_non_staff_with_allow_global_group_creation_disabled(
    data_fixture,
):
    # With group creation disabled, non-staff can't create groups.
    perm_manager = StaffOnlySettingOperationPermissionManagerType()
    user = data_fixture.create_user(is_staff=False)
    data_fixture.update_settings(allow_global_group_creation=False)
    with pytest.raises(PermissionException):
        perm_manager.check_permissions(user, CreateGroupOperationType.type)

    assert perm_manager.get_permissions_object(user) == {
        "staff_only_operations": [CreateGroupOperationType.type],
        "always_allowed_operations": [],
    }


@pytest.mark.django_db
def test_staff_setting_permission_manager_non_staff_with_allow_global_group_creation_enabled(
    data_fixture,
):
    # With group creation enabled, non-staff can create groups.
    perm_manager = StaffOnlySettingOperationPermissionManagerType()
    user = data_fixture.create_user(is_staff=False)
    data_fixture.update_settings(allow_global_group_creation=True)
    assert perm_manager.check_permissions(user, CreateGroupOperationType.type)
    assert perm_manager.get_permissions_object(user) == {
        "staff_only_operations": [],
        "always_allowed_operations": [CreateGroupOperationType.type],
    }
