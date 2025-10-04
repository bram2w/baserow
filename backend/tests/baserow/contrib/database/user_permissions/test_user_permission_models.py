"""
Tests for User Permission Models
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from baserow.contrib.database.user_permissions.models import (
    UserPermissionRule,
    UserFieldPermission,
    UserFilteredView,
    UserPermissionAuditLog,
)

User = get_user_model()


@pytest.mark.django_db
def test_user_permission_rule_creation(data_fixture):
    """Test creating a basic user permission rule"""
    user = data_fixture.create_user(email="test@example.com")
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create user permission rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.MANAGER,
        row_filter={"department": "{user.department}"},
        is_active=True
    )
    
    assert rule.table == table
    assert rule.user == user
    assert rule.role == UserPermissionRule.RoleChoices.MANAGER
    assert rule.row_filter == {"department": "{user.department}"}
    assert rule.is_active is True
    assert str(rule) == f"{user.email} - {table.name} (manager)"


@pytest.mark.django_db
def test_user_permission_rule_unique_constraint(data_fixture):
    """Test that only one permission rule per user-table is allowed"""
    user = data_fixture.create_user(email="test@example.com")
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create first rule
    UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER,
    )
    
    # Attempt to create duplicate should fail
    with pytest.raises(Exception):  # IntegrityError for unique constraint
        UserPermissionRule.objects.create(
            table=table,
            user=user,
            role=UserPermissionRule.RoleChoices.ADMIN,
        )


@pytest.mark.django_db
def test_user_permission_rule_role_permissions(data_fixture):
    """Test that role permissions return correct capabilities"""
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Test admin role permissions
    admin_rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.ADMIN
    )
    
    admin_perms = admin_rule.role_permissions
    assert admin_perms["can_read"] is True
    assert admin_perms["can_create"] is True
    assert admin_perms["can_update"] is True
    assert admin_perms["can_delete"] is True
    assert admin_perms["can_manage_permissions"] is True
    
    # Test viewer role permissions
    admin_rule.role = UserPermissionRule.RoleChoices.VIEWER
    admin_rule.save()
    
    viewer_perms = admin_rule.role_permissions
    assert viewer_perms["can_read"] is True
    assert viewer_perms["can_create"] is False
    assert viewer_perms["can_update"] is False
    assert viewer_perms["can_delete"] is False
    assert viewer_perms["can_manage_permissions"] is False


@pytest.mark.django_db
def test_user_permission_rule_clean_validation(data_fixture):
    """Test that clean() validates workspace membership"""
    user1 = data_fixture.create_user(email="user1@example.com")
    user2 = data_fixture.create_user(email="user2@example.com")
    
    workspace = data_fixture.create_workspace(user=user1)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Should work for workspace member
    rule = UserPermissionRule(
        table=table,
        user=user1,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    rule.clean()  # Should not raise
    
    # Should fail for non-workspace member
    rule_invalid = UserPermissionRule(
        table=table,
        user=user2,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    with pytest.raises(ValidationError, match="User must be a member of the workspace"):
        rule_invalid.clean()


@pytest.mark.django_db
def test_user_field_permission_creation(data_fixture):
    """Test creating field-specific permissions"""
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table, name="test_field")
    
    # Create user permission rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.MANAGER
    )
    
    # Create field permission
    field_perm = UserFieldPermission.objects.create(
        user_rule=rule,
        field=field,
        permission=UserFieldPermission.PermissionChoices.WRITE
    )
    
    assert field_perm.user_rule == rule
    assert field_perm.field == field
    assert field_perm.permission == UserFieldPermission.PermissionChoices.WRITE
    assert str(field_perm) == f"{field.name} - write ({user.email})"


@pytest.mark.django_db
def test_user_field_permission_validation(data_fixture):
    """Test field permission validation for table consistency"""
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    
    table1 = data_fixture.create_table_for_database(database=database, name="table1")
    table2 = data_fixture.create_table_for_database(database=database, name="table2")
    
    field1 = data_fixture.create_text_field(table=table1, name="field1")
    field2 = data_fixture.create_text_field(table=table2, name="field2")
    
    # Create permission rule for table1
    rule = UserPermissionRule.objects.create(
        table=table1,
        user=user,
        role=UserPermissionRule.RoleChoices.MANAGER
    )
    
    # Should work with field from same table
    field_perm1 = UserFieldPermission(
        user_rule=rule,
        field=field1,
        permission=UserFieldPermission.PermissionChoices.READ
    )
    field_perm1.clean()  # Should not raise
    
    # Should fail with field from different table
    field_perm2 = UserFieldPermission(
        user_rule=rule,
        field=field2,
        permission=UserFieldPermission.PermissionChoices.READ
    )
    
    with pytest.raises(ValidationError, match="Field must belong to the same table"):
        field_perm2.clean()


@pytest.mark.django_db
def test_user_filtered_view_creation(data_fixture):
    """Test creating user filtered views"""
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    view = data_fixture.create_grid_view(table=table)
    
    # Create user permission rule first
    UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.COORDINATOR
    )
    
    # Create filtered view
    filtered_view = UserFilteredView.objects.create(
        table=table,
        user=user,
        name="My Custom View",
        base_view=view,
        user_filters={"status": "active"},
        visible_fields=[1, 2, 3],
        is_default=True
    )
    
    assert filtered_view.table == table
    assert filtered_view.user == user
    assert filtered_view.name == "My Custom View"
    assert filtered_view.base_view == view
    assert filtered_view.user_filters == {"status": "active"}
    assert filtered_view.visible_fields == [1, 2, 3]
    assert filtered_view.is_default is True
    assert str(filtered_view) == f"My Custom View - {user.email} ({table.name})"


@pytest.mark.django_db
def test_user_filtered_view_validation(data_fixture):
    """Test user filtered view validation"""
    user1 = data_fixture.create_user()
    user2 = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user1)
    database = data_fixture.create_database_application(workspace=workspace)
    
    table1 = data_fixture.create_table_for_database(database=database)
    table2 = data_fixture.create_table_for_database(database=database)
    
    view1 = data_fixture.create_grid_view(table=table1)
    view2 = data_fixture.create_grid_view(table=table2)
    
    # Create permission rule for user1
    UserPermissionRule.objects.create(
        table=table1,
        user=user1,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    # Should work with matching table and base_view
    filtered_view1 = UserFilteredView(
        table=table1,
        user=user1,
        name="Valid View",
        base_view=view1
    )
    filtered_view1.clean()  # Should not raise
    
    # Should fail with mismatched table and base_view
    filtered_view2 = UserFilteredView(
        table=table1,
        user=user1,
        name="Invalid View",
        base_view=view2
    )
    
    with pytest.raises(ValidationError, match="Base view must belong to the same table"):
        filtered_view2.clean()
    
    # Should fail if user has no permissions on table
    filtered_view3 = UserFilteredView(
        table=table1,
        user=user2,
        name="No Permissions View"
    )
    
    with pytest.raises(ValidationError, match="User must have active permissions"):
        filtered_view3.clean()


@pytest.mark.django_db
def test_user_permission_audit_log(data_fixture):
    """Test audit logging functionality"""
    admin = data_fixture.create_user(email="admin@example.com")
    user = data_fixture.create_user(email="user@example.com")
    workspace = data_fixture.create_workspace(user=admin)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create audit log entry
    audit_log = UserPermissionAuditLog.objects.create(
        table=table,
        target_user=user,
        actor_user=admin,
        action=UserPermissionAuditLog.ActionChoices.GRANTED,
        details={
            "role": "manager",
            "row_filter": {"department": "IT"},
            "field_permissions_count": 3
        }
    )
    
    assert audit_log.table == table
    assert audit_log.target_user == user
    assert audit_log.actor_user == admin
    assert audit_log.action == UserPermissionAuditLog.ActionChoices.GRANTED
    assert audit_log.details["role"] == "manager"
    assert str(audit_log) == f"granted - {user.email} by {admin.email}"


@pytest.mark.django_db
def test_user_permission_rule_relationships(data_fixture):
    """Test model relationships and related_name functionality"""
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Create permission rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.COORDINATOR
    )
    
    # Create field permissions
    field_perm = UserFieldPermission.objects.create(
        user_rule=rule,
        field=field,
        permission=UserFieldPermission.PermissionChoices.HIDDEN
    )
    
    # Test relationships
    assert rule in table.user_permission_rules.all()
    assert rule in user.permission_rules.all()
    assert field_perm in rule.field_permissions.all()
    assert field_perm in field.user_permissions.all()
    
    # Test counts
    assert table.user_permission_rules.count() == 1
    assert user.permission_rules.count() == 1
    assert rule.field_permissions.count() == 1


@pytest.mark.django_db
def test_user_permission_rule_ordering(data_fixture):
    """Test that rules can be ordered using OrderableMixin"""
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    
    table1 = data_fixture.create_table_for_database(database=database, name="table1")
    table2 = data_fixture.create_table_for_database(database=database, name="table2")
    
    # Create rules with different orders
    rule1 = UserPermissionRule.objects.create(
        table=table1,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER,
        order=1.0
    )
    
    rule2 = UserPermissionRule.objects.create(
        table=table2,
        user=user,
        role=UserPermissionRule.RoleChoices.ADMIN,
        order=2.0
    )
    
    # Test ordering
    rules = user.permission_rules.order_by('order')
    assert list(rules) == [rule1, rule2]
    
    # Change order
    rule1.order = 3.0
    rule1.save()
    
    rules = user.permission_rules.order_by('order')
    assert list(rules) == [rule2, rule1]