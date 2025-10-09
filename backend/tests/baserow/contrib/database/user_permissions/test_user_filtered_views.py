"""
Tests for User Filtered Views
"""
import pytest
from django.contrib.auth import get_user_model

from baserow.contrib.database.user_permissions.models import (
    UserPermissionRule,
    UserFieldPermission,
    UserFilteredView,
)
from baserow.contrib.database.user_permissions.handler import UserPermissionHandler

User = get_user_model()


@pytest.mark.django_db
def test_user_filtered_view_automatic_creation(data_fixture):
    """Test that filtered view is created automatically when needed"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user(email="test@example.com")
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    base_view = data_fixture.create_grid_view(table=table, name="Base View")
    
    field1 = data_fixture.create_text_field(table=table, name="Visible Field")
    field2 = data_fixture.create_text_field(table=table, name="Hidden Field")
    
    # Create user permission rule with row filter
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.COORDINATOR,
        row_filter={"status": "active", "assigned_to": "{user.id}"}
    )
    
    # Create field permissions
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=field1,
        permission=UserFieldPermission.PermissionChoices.WRITE
    )
    
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=field2,
        permission=UserFieldPermission.PermissionChoices.HIDDEN
    )
    
    # Get filtered view (should be created automatically)
    filtered_view = handler.get_user_filtered_view(user, table, base_view)
    
    assert filtered_view is not None
    assert filtered_view.table == table
    assert filtered_view.user == user
    assert filtered_view.base_view == base_view
    assert filtered_view.name == f"My View - {table.name}"
    assert filtered_view.user_filters == {"status": "active", "assigned_to": "{user.id}"}
    assert filtered_view.is_default is True
    
    # Check visible fields (should include visible field, exclude hidden field)
    assert field1.id in filtered_view.visible_fields
    assert field2.id not in filtered_view.visible_fields


@pytest.mark.django_db
def test_user_filtered_view_existing_returned(data_fixture):
    """Test that existing filtered view is returned instead of creating new one"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create user permission rule
    UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    # Create existing filtered view
    existing_view = UserFilteredView.objects.create(
        table=table,
        user=user,
        name="Existing Custom View",
        user_filters={"custom": "filter"},
        visible_fields=[1, 2, 3],
        is_default=False
    )
    
    # Get filtered view
    result = handler.get_user_filtered_view(user, table)
    
    # Should return existing view, not create new one
    assert result == existing_view
    assert result.name == "Existing Custom View"
    assert result.user_filters == {"custom": "filter"}
    assert result.is_default is False
    
    # Verify no new view was created
    assert UserFilteredView.objects.filter(table=table, user=user).count() == 1


@pytest.mark.django_db
def test_user_filtered_view_no_permissions(data_fixture):
    """Test filtered view when user has no permissions"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # No user permission rule created
    
    result = handler.get_user_filtered_view(user, table)
    
    assert result is None


@pytest.mark.django_db
def test_user_filtered_view_field_visibility_logic(data_fixture):
    """Test field visibility logic in filtered views"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create multiple fields
    read_field = data_fixture.create_text_field(table=table, name="Read Only")
    write_field = data_fixture.create_text_field(table=table, name="Read Write")
    hidden_field = data_fixture.create_text_field(table=table, name="Hidden")
    default_field = data_fixture.create_text_field(table=table, name="Default")
    
    # Create user permission rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.MANAGER
    )
    
    # Create field permissions
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=read_field,
        permission=UserFieldPermission.PermissionChoices.READ
    )
    
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=write_field,
        permission=UserFieldPermission.PermissionChoices.WRITE
    )
    
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=hidden_field,
        permission=UserFieldPermission.PermissionChoices.HIDDEN
    )
    
    # No explicit permission for default_field (should default to READ)
    
    filtered_view = handler.get_user_filtered_view(user, table)
    
    # Check visible fields
    visible_fields = filtered_view.visible_fields
    
    assert read_field.id in visible_fields
    assert write_field.id in visible_fields
    assert default_field.id in visible_fields
    assert hidden_field.id not in visible_fields


@pytest.mark.django_db
def test_user_filtered_view_with_complex_row_filter(data_fixture):
    """Test filtered view with complex row filters"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user(
        id=123,
        email="manager@company.com",
        first_name="John",
        last_name="Manager"
    )
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create user permission rule with complex row filter
    complex_filter = {
        "assigned_to__in": ["{user.id}", "999"],  # User's tasks or unassigned
        "department": "{user.profile.department}",
        "status__in": ["active", "pending"],
        "created_by": "{user.id}",
        "public": True
    }
    
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.COORDINATOR,
        row_filter=complex_filter
    )
    
    filtered_view = handler.get_user_filtered_view(user, table)
    
    assert filtered_view.user_filters == complex_filter
    assert filtered_view.name == f"My View - {table.name}"


@pytest.mark.django_db
def test_user_filtered_view_inheritance_from_base_view(data_fixture):
    """Test that filtered view properly inherits from base view"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create base view with specific configuration
    base_view = data_fixture.create_grid_view(
        table=table,
        name="Team Overview"
    )
    
    # Create user permission rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER,
        row_filter={"team": "frontend"}
    )
    
    filtered_view = handler.get_user_filtered_view(user, table, base_view)
    
    assert filtered_view.base_view == base_view
    assert filtered_view.name == f"My View - {table.name}"
    assert filtered_view.user_filters == {"team": "frontend"}
    assert filtered_view.is_default is True


@pytest.mark.django_db
def test_user_filtered_view_multiple_users_same_table(data_fixture):
    """Test filtered views for multiple users on same table"""
    handler = UserPermissionHandler()
    
    user1 = data_fixture.create_user(email="user1@example.com")
    user2 = data_fixture.create_user(email="user2@example.com")
    workspace = data_fixture.create_workspace(user=user1)
    workspace.users.add(user2)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    field = data_fixture.create_text_field(table=table, name="Shared Field")
    
    # Create different permission rules for each user
    rule1 = UserPermissionRule.objects.create(
        table=table,
        user=user1,
        role=UserPermissionRule.RoleChoices.ADMIN,
        row_filter={"department": "engineering"}
    )
    
    rule2 = UserPermissionRule.objects.create(
        table=table,
        user=user2,
        role=UserPermissionRule.RoleChoices.VIEWER,
        row_filter={"department": "marketing"}
    )
    
    # Different field permissions
    UserFieldPermission.objects.create(
        user_rule=rule1,
        field=field,
        permission=UserFieldPermission.PermissionChoices.WRITE
    )
    
    UserFieldPermission.objects.create(
        user_rule=rule2,
        field=field,
        permission=UserFieldPermission.PermissionChoices.READ
    )
    
    # Get filtered views for both users
    view1 = handler.get_user_filtered_view(user1, table)
    view2 = handler.get_user_filtered_view(user2, table)
    
    # Verify they are different
    assert view1 != view2
    assert view1.user == user1
    assert view2.user == user2
    assert view1.user_filters == {"department": "engineering"}
    assert view2.user_filters == {"department": "marketing"}
    
    # Both should have the field visible but user permissions may differ in practice
    assert field.id in view1.visible_fields
    assert field.id in view2.visible_fields
    
    # Verify database state
    assert UserFilteredView.objects.filter(table=table).count() == 2
    assert UserFilteredView.objects.filter(table=table, user=user1).count() == 1
    assert UserFilteredView.objects.filter(table=table, user=user2).count() == 1


@pytest.mark.django_db
def test_user_filtered_view_updated_when_permissions_change(data_fixture):
    """Test that filtered view reflects permission changes"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Create initial permission rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER,
        row_filter={"status": "draft"}
    )
    
    # Initial field permission
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=field,
        permission=UserFieldPermission.PermissionChoices.READ
    )
    
    # Get initial filtered view
    view = handler.get_user_filtered_view(user, table)
    initial_filters = view.user_filters
    initial_visible_fields = view.visible_fields
    
    assert initial_filters == {"status": "draft"}
    assert field.id in initial_visible_fields
    
    # Update permissions
    rule.row_filter = {"status": "published"}
    rule.save()
    
    # Change field permission to hidden
    field_perm = UserFieldPermission.objects.get(user_rule=rule, field=field)
    field_perm.permission = UserFieldPermission.PermissionChoices.HIDDEN
    field_perm.save()
    
    # Delete existing view to force recreation
    UserFilteredView.objects.filter(table=table, user=user).delete()
    
    # Get updated filtered view
    updated_view = handler.get_user_filtered_view(user, table)
    
    assert updated_view.user_filters == {"status": "published"}
    assert field.id not in updated_view.visible_fields


@pytest.mark.django_db
def test_user_filtered_view_empty_row_filter(data_fixture):
    """Test filtered view with empty row filter"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create permission rule without row filter
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.MANAGER,
        row_filter={}  # Empty filter
    )
    
    filtered_view = handler.get_user_filtered_view(user, table)
    
    assert filtered_view.user_filters == {}
    assert filtered_view.name == f"My View - {table.name}"


@pytest.mark.django_db
def test_user_filtered_view_all_fields_visible_by_default(data_fixture):
    """Test that fields are visible by default when no explicit permissions"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create several fields
    field1 = data_fixture.create_text_field(table=table, name="Field 1")
    field2 = data_fixture.create_number_field(table=table, name="Field 2") 
    field3 = data_fixture.create_boolean_field(table=table, name="Field 3")
    
    # Create permission rule without field permissions
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.COORDINATOR
    )
    
    # No explicit field permissions created
    
    filtered_view = handler.get_user_filtered_view(user, table)
    
    # All fields should be visible by default
    visible_fields = filtered_view.visible_fields
    assert field1.id in visible_fields
    assert field2.id in visible_fields
    assert field3.id in visible_fields


@pytest.mark.django_db
def test_user_filtered_view_respects_trashed_fields(data_fixture):
    """Test that trashed fields are not included in visible fields"""
    handler = UserPermissionHandler()
    
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create fields
    active_field = data_fixture.create_text_field(table=table, name="Active Field")
    trashed_field = data_fixture.create_text_field(table=table, name="Trashed Field")
    
    # Trash one field
    trashed_field.trashed = True
    trashed_field.save()
    
    # Create permission rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    filtered_view = handler.get_user_filtered_view(user, table)
    
    # Only active field should be visible
    visible_fields = filtered_view.visible_fields
    assert active_field.id in visible_fields
    assert trashed_field.id not in visible_fields