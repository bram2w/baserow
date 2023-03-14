import pytest

from baserow.core.exceptions import PermissionException
from baserow.core.operations import CreateWorkspaceOperationType
from baserow.core.permission_manager import (
    StaffOnlySettingOperationPermissionManagerType,
)


@pytest.mark.django_db
def test_staff_setting_permission_manager_staff_with_allow_global_workspace_creation_disabled(
    data_fixture,
):
    # With workspace creation disabled, staff can still create workspaces.
    perm_manager = StaffOnlySettingOperationPermissionManagerType()
    user = data_fixture.create_user(is_staff=True)
    data_fixture.update_settings(allow_global_workspace_creation=False)
    assert perm_manager.check_permissions(user, CreateWorkspaceOperationType.type)
    assert perm_manager.get_permissions_object(user) == {
        "always_allowed_operations": [],
        "staff_only_operations": [CreateWorkspaceOperationType.type],
    }


@pytest.mark.django_db
def test_staff_setting_permission_manager_staff_with_allow_global_workspace_creation_enabled(
    data_fixture,
):
    # With workspace creation enabled, staff can still create workspaces.
    perm_manager = StaffOnlySettingOperationPermissionManagerType()
    user = data_fixture.create_user(is_staff=True)
    data_fixture.update_settings(allow_global_workspace_creation=True)
    assert perm_manager.check_permissions(user, CreateWorkspaceOperationType.type)
    assert perm_manager.get_permissions_object(user) == {
        "staff_only_operations": [],
        "always_allowed_operations": [CreateWorkspaceOperationType.type],
    }


@pytest.mark.django_db
def test_staff_setting_permission_manager_non_staff_with_allow_global_workspace_creation_disabled(
    data_fixture,
):
    # With workspace creation disabled, non-staff can't create workspaces.
    perm_manager = StaffOnlySettingOperationPermissionManagerType()
    user = data_fixture.create_user(is_staff=False)
    data_fixture.update_settings(allow_global_workspace_creation=False)
    with pytest.raises(PermissionException):
        perm_manager.check_permissions(user, CreateWorkspaceOperationType.type)

    assert perm_manager.get_permissions_object(user) == {
        "staff_only_operations": [CreateWorkspaceOperationType.type],
        "always_allowed_operations": [],
    }


@pytest.mark.django_db
def test_staff_setting_permission_manager_non_staff_with_allow_global_workspace_creation_enabled(
    data_fixture,
):
    # With workspace creation enabled, non-staff can create workspaces.
    perm_manager = StaffOnlySettingOperationPermissionManagerType()
    user = data_fixture.create_user(is_staff=False)
    data_fixture.update_settings(allow_global_workspace_creation=True)
    assert perm_manager.check_permissions(user, CreateWorkspaceOperationType.type)
    assert perm_manager.get_permissions_object(user) == {
        "staff_only_operations": [],
        "always_allowed_operations": [CreateWorkspaceOperationType.type],
    }
