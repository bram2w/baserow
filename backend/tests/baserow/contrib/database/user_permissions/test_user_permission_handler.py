"""
Tests for User Permission Handler
"""
import pytest
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from baserow.contrib.database.user_permissions.handler import UserPermissionHandler
from baserow.contrib.database.user_permissions.models import (
    UserPermissionRule,
    UserFieldPermission,
    UserFilteredView,
    UserPermissionAuditLog,
)
from baserow.contrib.database.user_permissions.exceptions import (
    UserPermissionRuleDoesNotExist,
    UserPermissionRuleAlreadyExists,
    InvalidUserContextVariable,
    InvalidRowFilter,
)
from baserow.core.exceptions import UserNotInWorkspace, PermissionDenied

User = get_user_model()


@pytest.mark.django_db
def test_get_user_permission_rule_success(data_fixture):
    """Test successfully getting a user permission rule"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create permission rule
    expected_rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.MANAGER,
        is_active=True
    )
    
    # Get the rule
    result = handler.get_user_permission_rule(table, user)
    
    assert result == expected_rule
    assert result.role == UserPermissionRule.RoleChoices.MANAGER


@pytest.mark.django_db
def test_get_user_permission_rule_not_found(data_fixture):
    """Test getting permission rule when none exists"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # No permission rule created
    result = handler.get_user_permission_rule(table, user)
    
    assert result is None


@pytest.mark.django_db
def test_get_user_permission_rule_inactive(data_fixture):
    """Test that inactive rules are not returned"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create inactive permission rule
    UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.MANAGER,
        is_active=False
    )
    
    result = handler.get_user_permission_rule(table, user)
    
    assert result is None


@pytest.mark.django_db
@patch('baserow.core.handler.CoreHandler.check_user_workspace_permissions')
def test_get_user_permission_rule_not_in_workspace(mock_check_perms, data_fixture):
    """Test exception when user not in workspace"""
    mock_check_perms.side_effect = UserNotInWorkspace()
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace()  # User not added to workspace
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    with pytest.raises(UserNotInWorkspace):
        handler.get_user_permission_rule(table, user)


@pytest.mark.django_db
@patch('baserow.contrib.database.user_permissions.handler.UserPermissionHandler._check_can_manage_permissions')
def test_grant_user_permission_success(mock_check_perms, data_fixture):
    """Test successfully granting user permission"""
    mock_check_perms.return_value = None  # Allow permission management
    handler = UserPermissionHandler()
    
    admin = data_fixture.create_user(email="admin@example.com")
    user = data_fixture.create_user(email="user@example.com")
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)  # Add user to workspace
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Grant permission with field permissions
    field_permissions = [
        {"field_id": field.id, "permission": "write"}
    ]
    
    rule = handler.grant_user_permission(
        actor=admin,
        table=table,
        user=user,
        role="manager",
        row_filter={"department": "{user.department}"},
        field_permissions=field_permissions
    )
    
    # Verify rule creation
    assert rule.table == table
    assert rule.user == user
    assert rule.role == "manager"
    assert rule.row_filter == {"department": "{user.department}"}
    assert rule.is_active is True
    
    # Verify field permission creation
    field_perms = rule.field_permissions.all()
    assert len(field_perms) == 1
    assert field_perms[0].field == field
    assert field_perms[0].permission == "write"
    
    # Verify audit log
    audit_logs = UserPermissionAuditLog.objects.filter(
        table=table,
        target_user=user,
        actor_user=admin
    )
    assert len(audit_logs) == 1
    assert audit_logs[0].action == UserPermissionAuditLog.ActionChoices.GRANTED


@pytest.mark.django_db
def test_grant_user_permission_already_exists(data_fixture):
    """Test exception when user already has permission rule"""
    handler = UserPermissionHandler()
    
    admin = data_fixture.create_user(email="admin@example.com")
    user = data_fixture.create_user(email="user@example.com")
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create existing rule
    UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    with patch.object(handler, '_check_can_manage_permissions'):
        with pytest.raises(UserPermissionRuleAlreadyExists):
            handler.grant_user_permission(
                actor=admin,
                table=table,
                user=user,
                role="manager"
            )


@pytest.mark.django_db
def test_validate_row_filter_success(data_fixture):
    """Test successful row filter validation"""
    handler = UserPermissionHandler()
    
    # Valid filters should not raise
    valid_filters = [
        {"assigned_to": "{user.id}"},
        {"department": "{user.profile.department}"},
        {"status": "active", "owner": "{user.email}"},
        {"group__in": "{user.groups}"},
    ]
    
    for filter_dict in valid_filters:
        handler._validate_row_filter(filter_dict)  # Should not raise


@pytest.mark.django_db
def test_validate_row_filter_invalid_variable(data_fixture):
    """Test row filter validation with invalid variables"""
    handler = UserPermissionHandler()
    
    invalid_filters = [
        {"field": "{user.password}"},  # Not allowed
        {"field": "{user.invalid_attr}"},  # Not in allowed list
        {"field": "{system.secret}"},  # Wrong namespace
        {"field": "{user.groups.admin}"},  # Nested access not allowed
    ]
    
    for filter_dict in invalid_filters:
        with pytest.raises(InvalidUserContextVariable):
            handler._validate_row_filter(filter_dict)


@pytest.mark.django_db
def test_resolve_user_variables(data_fixture):
    """Test resolving user variables in filters"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user(
        email="john@example.com",
        first_name="John",
        last_name="Doe"
    )
    # Mock user profile with department
    user.profile = MagicMock()
    user.profile.department = "Engineering"
    
    # Mock user groups
    user.groups = MagicMock()
    user.groups.values_list.return_value = ["developers", "staff"]
    
    filter_input = {
        "assigned_to": "{user.id}",
        "email": "{user.email}",
        "department": "{user.profile.department}",
        "groups__in": "{user.groups}",
        "is_staff": "{user.is_staff}",
        "static_value": "unchanged"
    }
    
    resolved = handler._resolve_user_variables(filter_input, user)
    
    assert resolved["assigned_to"] == user.id
    assert resolved["email"] == user.email
    assert resolved["department"] == "Engineering"
    assert resolved["groups__in"] == ["developers", "staff"]
    assert resolved["is_staff"] == user.is_staff
    assert resolved["static_value"] == "unchanged"


@pytest.mark.django_db
@patch('baserow.contrib.database.user_permissions.handler.UserPermissionHandler._check_can_manage_permissions')
def test_update_user_permission_success(mock_check_perms, data_fixture):
    """Test successfully updating user permission"""
    mock_check_perms.return_value = None
    handler = UserPermissionHandler()
    
    admin = data_fixture.create_user(email="admin@example.com")
    user = data_fixture.create_user(email="user@example.com")
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Create initial rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER,
        row_filter={"old": "filter"}
    )
    
    # Update permission
    new_field_permissions = [
        {"field_id": field.id, "permission": "hidden"}
    ]
    
    updated_rule = handler.update_user_permission(
        actor=admin,
        table=table,
        user=user,
        role="manager",
        row_filter={"new": "filter"},
        field_permissions=new_field_permissions
    )
    
    # Verify updates
    assert updated_rule.role == "manager"
    assert updated_rule.row_filter == {"new": "filter"}
    
    # Verify field permissions updated
    field_perms = updated_rule.field_permissions.all()
    assert len(field_perms) == 1
    assert field_perms[0].permission == "hidden"
    
    # Verify audit log
    audit_logs = UserPermissionAuditLog.objects.filter(
        action=UserPermissionAuditLog.ActionChoices.MODIFIED
    )
    assert len(audit_logs) == 1


@pytest.mark.django_db
def test_update_user_permission_not_exists(data_fixture):
    """Test updating non-existent permission rule"""
    handler = UserPermissionHandler()
    
    admin = data_fixture.create_user()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    with patch.object(handler, '_check_can_manage_permissions'):
        with pytest.raises(UserPermissionRuleDoesNotExist):
            handler.update_user_permission(
                actor=admin,
                table=table,
                user=user,
                role="admin"
            )


@pytest.mark.django_db
@patch('baserow.contrib.database.user_permissions.handler.UserPermissionHandler._check_can_manage_permissions')
def test_revoke_user_permission_success(mock_check_perms, data_fixture):
    """Test successfully revoking user permission"""
    mock_check_perms.return_value = None
    handler = UserPermissionHandler()
    
    admin = data_fixture.create_user()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create rule to revoke
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.MANAGER,
        is_active=True
    )
    
    # Create filtered view to be deleted
    UserFilteredView.objects.create(
        table=table,
        user=user,
        name="User View"
    )
    
    result = handler.revoke_user_permission(
        actor=admin,
        table=table,
        user=user
    )
    
    # Verify revocation (soft delete)
    assert result is True
    rule.refresh_from_db()
    assert rule.is_active is False
    
    # Verify filtered view deleted
    assert UserFilteredView.objects.filter(table=table, user=user).count() == 0
    
    # Verify audit log
    audit_logs = UserPermissionAuditLog.objects.filter(
        action=UserPermissionAuditLog.ActionChoices.REVOKED
    )
    assert len(audit_logs) == 1


@pytest.mark.django_db
def test_revoke_user_permission_not_exists(data_fixture):
    """Test revoking non-existent permission"""
    handler = UserPermissionHandler()
    
    admin = data_fixture.create_user()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    with patch.object(handler, '_check_can_manage_permissions'):
        result = handler.revoke_user_permission(
            actor=admin,
            table=table,
            user=user
        )
        
        assert result is False


@pytest.mark.django_db
def test_get_effective_permissions_no_rule(data_fixture):
    """Test effective permissions when no user rule exists"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    with patch('baserow.core.handler.CoreHandler.check_permissions') as mock_check:
        mock_check.return_value = True
        
        permissions = handler.get_effective_permissions(user, table)
        
        # Should return base permissions when no user rule
        assert permissions['can_read'] is True
        assert permissions['can_create'] is True
        assert permissions['can_update'] is True
        assert permissions['has_row_filter'] is False


@pytest.mark.django_db
def test_get_effective_permissions_with_rule(data_fixture):
    """Test effective permissions with user rule"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Create user rule with restrictions
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER,
        row_filter={"department": "IT"}
    )
    
    # Create field permission
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=field,
        permission=UserFieldPermission.PermissionChoices.HIDDEN
    )
    
    with patch('baserow.core.handler.CoreHandler.check_permissions') as mock_check:
        mock_check.return_value = True
        
        permissions = handler.get_effective_permissions(user, table)
        
        # Should reflect viewer role permissions
        assert permissions['can_read'] is True
        assert permissions['can_create'] is False
        assert permissions['can_update'] is False
        assert permissions['can_delete'] is False
        assert permissions['has_row_filter'] is True
        assert permissions['row_filter'] == {"department": "IT"}
        
        # Field should not be in visible fields (it's hidden)
        assert field.id not in permissions['visible_fields']


@pytest.mark.django_db
def test_apply_row_filters(data_fixture):
    """Test applying row filters to queryset"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user(id=123, email="test@example.com")
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create user rule with row filter
    UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER,
        row_filter={"assigned_to": "{user.id}", "status": "active"}
    )
    
    # Mock queryset
    mock_queryset = MagicMock()
    mock_filtered_queryset = MagicMock()
    mock_queryset.filter.return_value = mock_filtered_queryset
    
    result = handler.apply_row_filters(user, table, mock_queryset)
    
    # Should call filter with resolved variables
    mock_queryset.filter.assert_called_once_with(
        assigned_to=123,
        status="active"
    )
    assert result == mock_filtered_queryset


@pytest.mark.django_db
def test_apply_row_filters_no_rule(data_fixture):
    """Test applying filters when no user rule exists"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # No user rule created
    
    mock_queryset = MagicMock()
    
    result = handler.apply_row_filters(user, table, mock_queryset)
    
    # Should return original queryset unchanged
    assert result == mock_queryset
    mock_queryset.filter.assert_not_called()


@pytest.mark.django_db
def test_get_user_filtered_view_create(data_fixture):
    """Test creating user filtered view automatically"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    base_view = data_fixture.create_grid_view(table=table)
    field = data_fixture.create_text_field(table=table)
    
    # Create user rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.COORDINATOR,
        row_filter={"type": "public"}
    )
    
    # Create field permission to test visible fields
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=field,
        permission=UserFieldPermission.PermissionChoices.READ
    )
    
    filtered_view = handler.get_user_filtered_view(user, table, base_view)
    
    assert filtered_view is not None
    assert filtered_view.table == table
    assert filtered_view.user == user
    assert filtered_view.base_view == base_view
    assert filtered_view.user_filters == {"type": "public"}
    assert field.id in filtered_view.visible_fields
    assert filtered_view.is_default is True


@pytest.mark.django_db
def test_get_user_filtered_view_existing(data_fixture):
    """Test getting existing user filtered view"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create user rule
    UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    # Create existing filtered view
    existing_view = UserFilteredView.objects.create(
        table=table,
        user=user,
        name="Existing View",
        user_filters={"existing": "filter"},
        visible_fields=[1, 2]
    )
    
    result = handler.get_user_filtered_view(user, table)
    
    assert result == existing_view
    assert result.name == "Existing View"


@pytest.mark.django_db
def test_get_user_filtered_view_no_permissions(data_fixture):
    """Test getting filtered view when user has no permissions"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # No user rule created
    
    result = handler.get_user_filtered_view(user, table)
    
    assert result is None


@pytest.mark.django_db 
def test_check_can_manage_permissions_success(data_fixture):
    """Test successful permission management check"""
    handler = UserPermissionHandler()
    
    admin = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create admin rule
    UserPermissionRule.objects.create(
        table=table,
        user=admin,
        role=UserPermissionRule.RoleChoices.ADMIN
    )
    
    with patch('baserow.core.handler.CoreHandler.check_permissions') as mock_check:
        mock_check.return_value = True
        
        # Should not raise
        handler._check_can_manage_permissions(admin, table)


@pytest.mark.django_db
def test_check_can_manage_permissions_non_admin(data_fixture):
    """Test permission management check for non-admin user"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create non-admin rule
    UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    with patch('baserow.core.handler.CoreHandler.check_permissions') as mock_check:
        mock_check.return_value = True
        
        with pytest.raises(PermissionDenied):
            handler._check_can_manage_permissions(user, table)