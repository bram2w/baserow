"""
Tests for User Permission Manager Type
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from unittest.mock import patch, MagicMock

from baserow.contrib.database.user_permissions.permission_manager_types import UserPermissionManagerType
from baserow.contrib.database.user_permissions.models import UserPermissionRule, UserFieldPermission

User = get_user_model()


@pytest.mark.django_db
def test_user_permission_manager_type_initialization():
    """Test UserPermissionManagerType initialization"""
    manager = UserPermissionManagerType()
    
    assert manager.type == "user_permissions"
    assert hasattr(manager, 'handler')


@pytest.mark.django_db
def test_get_permissions_object_anonymous_user():
    """Test permissions object for anonymous user"""
    manager = UserPermissionManagerType()
    
    permissions = manager.get_permissions_object(AnonymousUser())
    
    assert permissions['can_read'] is False
    assert permissions['can_create'] is False
    assert permissions['can_update'] is False
    assert permissions['can_delete'] is False
    assert permissions['can_manage_permissions'] is False
    assert permissions['visible_fields'] == []
    assert permissions['has_row_filter'] is False


@pytest.mark.django_db
def test_get_permissions_object_no_context(data_fixture):
    """Test permissions object with no context"""
    manager = UserPermissionManagerType()
    user = data_fixture.create_user()
    
    permissions = manager.get_permissions_object(user)
    
    # Should return base permissions when no context
    assert permissions['can_read'] is True
    assert permissions['can_create'] is True
    assert permissions['can_update'] is True
    assert permissions['can_delete'] is True
    assert permissions['can_manage_permissions'] is True


@pytest.mark.django_db
@patch('baserow.contrib.database.user_permissions.handler.UserPermissionHandler.get_effective_permissions')
def test_get_permissions_object_with_table_context(mock_get_perms, data_fixture):
    """Test permissions object with table in context"""
    mock_get_perms.return_value = {
        'can_read': True,
        'can_create': False,
        'can_update': False,
        'can_delete': False,
        'can_manage_permissions': False,
        'visible_fields': [1, 2, 3],
        'has_row_filter': True,
        'row_filter': {'department': 'IT'}
    }
    
    manager = UserPermissionManagerType()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    context = {'table': table}
    permissions = manager.get_permissions_object(user, context=context)
    
    assert permissions['can_read'] is True
    assert permissions['can_create'] is False
    assert permissions['visible_fields'] == [1, 2, 3]
    assert permissions['has_row_filter'] is True
    mock_get_perms.assert_called_once_with(user, table)


@pytest.mark.django_db
def test_get_permissions_object_with_field_context(data_fixture):
    """Test permissions object with field in context"""
    manager = UserPermissionManagerType()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    context = {'field': field}
    
    with patch.object(manager.handler, 'get_effective_permissions') as mock_get_perms:
        mock_get_perms.return_value = {
            'can_read': True,
            'can_create': True,
            'visible_fields': [field.id],
            'has_row_filter': False,
            'row_filter': {}
        }
        
        permissions = manager.get_permissions_object(user, context=context)
        
        mock_get_perms.assert_called_once_with(user, table)
        assert permissions['can_read'] is True


@pytest.mark.django_db
def test_check_permissions_anonymous_user():
    """Test check_permissions for anonymous user"""
    manager = UserPermissionManagerType()
    
    result = manager.check_permissions(
        AnonymousUser(),
        'database.table.read',
        context={'table': MagicMock()}
    )
    
    assert result is False


@pytest.mark.django_db
def test_check_permissions_no_context(data_fixture):
    """Test check_permissions with no context"""
    manager = UserPermissionManagerType()
    user = data_fixture.create_user()
    
    result = manager.check_permissions(user, 'database.table.read')
    
    # Should return True (delegate to other managers) when no context
    assert result is True


@pytest.mark.django_db
def test_check_permissions_no_user_rule(data_fixture):
    """Test check_permissions when no user rule exists"""
    manager = UserPermissionManagerType()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    context = {'table': table}
    
    with patch.object(manager.handler, 'get_user_permission_rule') as mock_get_rule:
        mock_get_rule.return_value = None
        
        result = manager.check_permissions(user, 'database.table.read', context=context)
        
        # Should return True (delegate) when no user rule
        assert result is True


@pytest.mark.django_db
def test_check_permissions_with_user_rule_allowed(data_fixture):
    """Test check_permissions with user rule that allows operation"""
    manager = UserPermissionManagerType()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create user rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.MANAGER
    )
    
    context = {'table': table}
    
    with patch.object(manager.handler, 'get_effective_permissions') as mock_get_perms:
        mock_get_perms.return_value = {
            'can_read': True,
            'can_create': True,
            'can_update': True,
            'can_delete': False
        }
        
        # Test allowed operation
        result = manager.check_permissions(user, 'database.table.read', context=context)
        assert result is True
        
        # Test another allowed operation
        result = manager.check_permissions(user, 'database.rows.update', context=context)
        assert result is True
        
        # Test forbidden operation
        result = manager.check_permissions(user, 'database.rows.delete', context=context)
        assert result is False


@pytest.mark.django_db
def test_check_permissions_field_level(data_fixture):
    """Test check_permissions at field level"""
    manager = UserPermissionManagerType()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Create user rule with field permission
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=field,
        permission=UserFieldPermission.PermissionChoices.HIDDEN
    )
    
    context = {'table': table, 'field': field}
    
    with patch.object(manager.handler, 'get_effective_permissions') as mock_get_perms:
        mock_get_perms.return_value = {
            'can_read': True,
            'visible_fields': []  # Field is hidden, so not in visible fields
        }
        
        result = manager.check_permissions(user, 'database.table.read', context=context)
        
        # Should be False because field is hidden
        assert result is False


@pytest.mark.django_db
def test_check_permissions_field_level_visible(data_fixture):
    """Test check_permissions for visible field"""
    manager = UserPermissionManagerType()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Create user rule with visible field permission
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.COORDINATOR
    )
    
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=field,
        permission=UserFieldPermission.PermissionChoices.WRITE
    )
    
    context = {'table': table, 'field': field}
    
    with patch.object(manager.handler, 'get_effective_permissions') as mock_get_perms:
        mock_get_perms.return_value = {
            'can_read': True,
            'can_update': True,
            'visible_fields': [field.id]  # Field is visible
        }
        
        result = manager.check_permissions(user, 'database.rows.update', context=context)
        
        # Should be True because field is visible and user has update permission
        assert result is True


@pytest.mark.django_db
def test_filter_queryset_anonymous_user():
    """Test filter_queryset for anonymous user"""
    manager = UserPermissionManagerType()
    mock_queryset = MagicMock()
    mock_queryset.none.return_value = "empty_queryset"
    
    result = manager.filter_queryset(
        AnonymousUser(),
        'database.rows.read',
        mock_queryset
    )
    
    assert result == "empty_queryset"
    mock_queryset.none.assert_called_once()


@pytest.mark.django_db
def test_filter_queryset_not_row_queryset(data_fixture):
    """Test filter_queryset for non-row queryset"""
    manager = UserPermissionManagerType()
    user = data_fixture.create_user()
    mock_queryset = MagicMock()
    mock_queryset.model = MagicMock()
    # Mock queryset that doesn't have 'table' attribute
    del mock_queryset.model.table
    
    result = manager.filter_queryset(user, 'database.rows.read', mock_queryset)
    
    # Should return original queryset unchanged
    assert result == mock_queryset


@pytest.mark.django_db
def test_filter_queryset_row_queryset(data_fixture):
    """Test filter_queryset for row queryset"""
    manager = UserPermissionManagerType()
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Mock row queryset
    mock_queryset = MagicMock()
    mock_queryset.model.table = table
    
    filtered_queryset = MagicMock()
    
    with patch.object(manager.handler, 'apply_row_filters') as mock_apply_filters:
        mock_apply_filters.return_value = filtered_queryset
        
        result = manager.filter_queryset(user, 'database.rows.read', mock_queryset)
        
        mock_apply_filters.assert_called_once_with(user, table, mock_queryset)
        assert result == filtered_queryset


@pytest.mark.django_db
def test_get_role_assignments_no_context():
    """Test get_role_assignments with no context"""
    manager = UserPermissionManagerType()
    
    result = manager.get_role_assignments()
    
    assert result == {}


@pytest.mark.django_db
def test_get_role_assignments_no_table_context():
    """Test get_role_assignments with context but no table"""
    manager = UserPermissionManagerType()
    
    result = manager.get_role_assignments(context={'field': 'something'})
    
    assert result == {}


@pytest.mark.django_db
def test_get_role_assignments_with_table(data_fixture):
    """Test get_role_assignments with table context"""
    manager = UserPermissionManagerType()
    
    user1 = data_fixture.create_user(email="user1@example.com")
    user2 = data_fixture.create_user(email="user2@example.com")
    workspace = data_fixture.create_workspace(user=user1)
    workspace.users.add(user2)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Create user rules
    rule1 = UserPermissionRule.objects.create(
        table=table,
        user=user1,
        role=UserPermissionRule.RoleChoices.ADMIN,
        row_filter={"department": "IT"}
    )
    
    rule2 = UserPermissionRule.objects.create(
        table=table,
        user=user2,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    # Add field permissions
    UserFieldPermission.objects.create(
        user_rule=rule1,
        field=field,
        permission=UserFieldPermission.PermissionChoices.WRITE
    )
    
    context = {'table': table}
    result = manager.get_role_assignments(context=context)
    
    assert len(result) == 2
    
    # Check user1 assignment
    user1_assignment = result['user1@example.com']
    assert user1_assignment['role'] == UserPermissionRule.RoleChoices.ADMIN
    assert user1_assignment['has_row_filter'] is True
    assert user1_assignment['field_permissions_count'] == 1
    assert user1_assignment['permissions']['can_manage_permissions'] is True
    
    # Check user2 assignment  
    user2_assignment = result['user2@example.com']
    assert user2_assignment['role'] == UserPermissionRule.RoleChoices.VIEWER
    assert user2_assignment['has_row_filter'] is False
    assert user2_assignment['field_permissions_count'] == 0
    assert user2_assignment['permissions']['can_manage_permissions'] is False


@pytest.mark.django_db
def test_extract_table_from_context_direct_table(data_fixture):
    """Test extracting table directly from context"""
    manager = UserPermissionManagerType()
    workspace = data_fixture.create_workspace()
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    context = {'table': table}
    result = manager._extract_table_from_context(context)
    
    assert result == table


@pytest.mark.django_db
def test_extract_table_from_context_via_field(data_fixture):
    """Test extracting table via field in context"""
    manager = UserPermissionManagerType()
    workspace = data_fixture.create_workspace()
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    context = {'field': field}
    result = manager._extract_table_from_context(context)
    
    assert result == table


@pytest.mark.django_db
def test_extract_table_from_context_via_row(data_fixture):
    """Test extracting table via row in context"""
    manager = UserPermissionManagerType()
    
    # Mock row with table attribute
    mock_row = MagicMock()
    mock_table = MagicMock()
    mock_row.table = mock_table
    
    context = {'row': mock_row}
    result = manager._extract_table_from_context(context)
    
    assert result == mock_table


@pytest.mark.django_db
def test_extract_table_from_context_not_found():
    """Test extracting table when not in context"""
    manager = UserPermissionManagerType()
    
    context = {'other': 'value'}
    result = manager._extract_table_from_context(context)
    
    assert result is None


@pytest.mark.django_db
def test_check_operation_permission_mapping():
    """Test operation to permission mapping"""
    manager = UserPermissionManagerType()
    
    permissions = {
        'can_read': True,
        'can_create': False,
        'can_update': True,
        'can_delete': False
    }
    
    # Test read operations
    assert manager._check_operation_permission('database.table.read', permissions, {}) is True
    assert manager._check_operation_permission('database.rows.read', permissions, {}) is True
    
    # Test create operations
    assert manager._check_operation_permission('database.table.create', permissions, {}) is False
    assert manager._check_operation_permission('database.rows.create', permissions, {}) is False
    
    # Test update operations
    assert manager._check_operation_permission('database.table.update', permissions, {}) is True
    assert manager._check_operation_permission('database.rows.update', permissions, {}) is True
    
    # Test delete operations
    assert manager._check_operation_permission('database.table.delete', permissions, {}) is False
    assert manager._check_operation_permission('database.rows.delete', permissions, {}) is False
    
    # Test unknown operation
    assert manager._check_operation_permission('unknown.operation', permissions, {}) is True