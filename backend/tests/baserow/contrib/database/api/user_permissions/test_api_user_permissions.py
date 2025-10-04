"""
API Tests for User Permissions
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from baserow.contrib.database.user_permissions.models import (
    UserPermissionRule,
    UserFieldPermission,
    UserFilteredView,
    UserPermissionAuditLog,
)

User = get_user_model()


@pytest.mark.django_db
def test_list_user_permission_rules(api_client, data_fixture):
    """Test listing user permission rules for a table"""
    admin = data_fixture.create_user(email="admin@example.com")
    user1 = data_fixture.create_user(email="user1@example.com")
    user2 = data_fixture.create_user(email="user2@example.com")
    
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user1, user2)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create permission rules
    rule1 = UserPermissionRule.objects.create(
        table=table,
        user=user1,
        role=UserPermissionRule.RoleChoices.MANAGER
    )
    
    rule2 = UserPermissionRule.objects.create(
        table=table,
        user=user2,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    # Admin rule to allow permission management
    UserPermissionRule.objects.create(
        table=table,
        user=admin,
        role=UserPermissionRule.RoleChoices.ADMIN
    )
    
    url = reverse(
        "api:database:user_permissions:list_create",
        kwargs={"table_id": table.id}
    )
    
    api_client.force_authenticate(user=admin)
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 3  # All three rules
    
    # Check rule details
    rules_data = {rule["user"]["id"]: rule for rule in response.json()}
    
    assert rules_data[user1.id]["role"] == "manager"
    assert rules_data[user2.id]["role"] == "viewer"
    assert rules_data[admin.id]["role"] == "admin"


@pytest.mark.django_db
def test_create_user_permission_rule(api_client, data_fixture):
    """Test creating a new user permission rule"""
    admin = data_fixture.create_user(email="admin@example.com")
    user = data_fixture.create_user(email="user@example.com")
    
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Admin rule to allow permission management
    UserPermissionRule.objects.create(
        table=table,
        user=admin,
        role=UserPermissionRule.RoleChoices.ADMIN
    )
    
    url = reverse(
        "api:database:user_permissions:list_create",
        kwargs={"table_id": table.id}
    )
    
    data = {
        "user_id": user.id,
        "role": "manager",
        "row_filter": {
            "department": "{user.department}",
            "status": "active"
        },
        "field_permissions": [
            {
                "field_id": field.id,
                "permission": "write"
            }
        ]
    }
    
    api_client.force_authenticate(user=admin)
    response = api_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    
    response_data = response.json()
    assert response_data["user"]["id"] == user.id
    assert response_data["role"] == "manager"
    assert response_data["row_filter"]["department"] == "{user.department}"
    assert response_data["effective_permissions"]["can_read"] is True
    assert response_data["effective_permissions"]["can_update"] is True
    assert response_data["effective_permissions"]["can_delete"] is False
    
    # Verify rule was created in database
    rule = UserPermissionRule.objects.get(table=table, user=user)
    assert rule.role == "manager"
    assert rule.row_filter == {"department": "{user.department}", "status": "active"}
    
    # Verify field permission was created
    field_perm = UserFieldPermission.objects.get(user_rule=rule, field=field)
    assert field_perm.permission == "write"
    
    # Verify audit log was created
    audit_log = UserPermissionAuditLog.objects.get(
        table=table,
        target_user=user,
        actor_user=admin,
        action=UserPermissionAuditLog.ActionChoices.GRANTED
    )
    assert audit_log.details["role"] == "manager"


@pytest.mark.django_db
def test_create_user_permission_rule_already_exists(api_client, data_fixture):
    """Test creating user permission rule when one already exists"""
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
    
    # Admin rule to allow permission management
    UserPermissionRule.objects.create(
        table=table,
        user=admin,
        role=UserPermissionRule.RoleChoices.ADMIN
    )
    
    url = reverse(
        "api:database:user_permissions:list_create",
        kwargs={"table_id": table.id}
    )
    
    data = {
        "user_id": user.id,
        "role": "manager"
    }
    
    api_client.force_authenticate(user=admin)
    response = api_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_PERMISSION_RULE_ALREADY_EXISTS"


@pytest.mark.django_db
def test_create_user_permission_rule_invalid_row_filter(api_client, data_fixture):
    """Test creating user permission rule with invalid row filter"""
    admin = data_fixture.create_user(email="admin@example.com")
    user = data_fixture.create_user(email="user@example.com")
    
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Admin rule to allow permission management
    UserPermissionRule.objects.create(
        table=table,
        user=admin,
        role=UserPermissionRule.RoleChoices.ADMIN
    )
    
    url = reverse(
        "api:database:user_permissions:list_create",
        kwargs={"table_id": table.id}
    )
    
    data = {
        "user_id": user.id,
        "role": "manager",
        "row_filter": {
            "password": "{user.password}",  # Invalid variable
        }
    }
    
    api_client.force_authenticate(user=admin)
    response = api_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid row filter" in response.json()["row_filter"][0]


@pytest.mark.django_db
def test_get_user_permission_rule(api_client, data_fixture):
    """Test getting details of a user permission rule"""
    admin = data_fixture.create_user(email="admin@example.com")
    user = data_fixture.create_user(email="user@example.com")
    
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Create user rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.COORDINATOR,
        row_filter={"team": "frontend"}
    )
    
    # Create field permission
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=field,
        permission=UserFieldPermission.PermissionChoices.HIDDEN
    )
    
    url = reverse(
        "api:database:user_permissions:detail",
        kwargs={"table_id": table.id, "user_id": user.id}
    )
    
    api_client.force_authenticate(user=admin)
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    
    response_data = response.json()
    assert response_data["user"]["id"] == user.id
    assert response_data["role"] == "coordinator"
    assert response_data["row_filter"]["team"] == "frontend"
    assert response_data["effective_permissions"]["can_read"] is True
    assert response_data["effective_permissions"]["can_create"] is True
    assert response_data["effective_permissions"]["can_delete"] is False


@pytest.mark.django_db
def test_update_user_permission_rule(api_client, data_fixture):
    """Test updating an existing user permission rule"""
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
    
    # Admin rule to allow permission management
    UserPermissionRule.objects.create(
        table=table,
        user=admin,
        role=UserPermissionRule.RoleChoices.ADMIN
    )
    
    url = reverse(
        "api:database:user_permissions:detail",
        kwargs={"table_id": table.id, "user_id": user.id}
    )
    
    data = {
        "role": "manager",
        "row_filter": {"new": "filter"},
        "field_permissions": [
            {
                "field_id": field.id,
                "permission": "write"
            }
        ]
    }
    
    api_client.force_authenticate(user=admin)
    response = api_client.patch(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    
    response_data = response.json()
    assert response_data["role"] == "manager"
    assert response_data["row_filter"]["new"] == "filter"
    
    # Verify changes in database
    rule.refresh_from_db()
    assert rule.role == "manager"
    assert rule.row_filter == {"new": "filter"}
    
    # Verify field permission was updated
    field_perm = UserFieldPermission.objects.get(user_rule=rule, field=field)
    assert field_perm.permission == "write"
    
    # Verify audit log
    audit_log = UserPermissionAuditLog.objects.get(
        table=table,
        target_user=user,
        actor_user=admin,
        action=UserPermissionAuditLog.ActionChoices.MODIFIED
    )
    assert audit_log.details["role"] == "manager"


@pytest.mark.django_db
def test_revoke_user_permission_rule(api_client, data_fixture):
    """Test revoking user permissions"""
    admin = data_fixture.create_user(email="admin@example.com")
    user = data_fixture.create_user(email="user@example.com")
    
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create user rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.MANAGER
    )
    
    # Create filtered view
    UserFilteredView.objects.create(
        table=table,
        user=user,
        name="User View"
    )
    
    # Admin rule to allow permission management
    UserPermissionRule.objects.create(
        table=table,
        user=admin,
        role=UserPermissionRule.RoleChoices.ADMIN
    )
    
    url = reverse(
        "api:database:user_permissions:detail",
        kwargs={"table_id": table.id, "user_id": user.id}
    )
    
    api_client.force_authenticate(user=admin)
    response = api_client.delete(url)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify rule was soft-deleted
    rule.refresh_from_db()
    assert rule.is_active is False
    
    # Verify filtered view was deleted
    assert UserFilteredView.objects.filter(table=table, user=user).count() == 0
    
    # Verify audit log
    audit_log = UserPermissionAuditLog.objects.get(
        table=table,
        target_user=user,
        actor_user=admin,
        action=UserPermissionAuditLog.ActionChoices.REVOKED
    )
    assert audit_log.details["previous_role"] == "manager"


@pytest.mark.django_db
def test_get_user_permissions_summary(api_client, data_fixture):
    """Test getting comprehensive user permissions summary"""
    user = data_fixture.create_user(email="user@example.com")
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Create user rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.COORDINATOR,
        row_filter={"department": "engineering"}
    )
    
    # Create field permission
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=field,
        permission=UserFieldPermission.PermissionChoices.READ
    )
    
    url = reverse(
        "api:database:user_permissions:summary",
        kwargs={"table_id": table.id, "user_id": user.id}
    )
    
    api_client.force_authenticate(user=user)
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    
    response_data = response.json()
    assert response_data["user"]["id"] == user.id
    assert response_data["table"]["id"] == table.id
    assert response_data["has_permissions"] is True
    assert response_data["rule"]["role"] == "coordinator"
    assert len(response_data["field_permissions"]) == 1
    assert response_data["field_permissions"][0]["permission"] == "read"
    assert response_data["effective_permissions"]["can_read"] is True
    assert response_data["effective_permissions"]["can_create"] is True
    assert response_data["effective_permissions"]["can_delete"] is False


@pytest.mark.django_db
def test_get_user_filtered_view(api_client, data_fixture):
    """Test getting user's filtered view"""
    user = data_fixture.create_user(email="user@example.com")
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    field = data_fixture.create_text_field(table=table)
    
    # Create user rule
    rule = UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.VIEWER,
        row_filter={"status": "published"}
    )
    
    # Field permission
    UserFieldPermission.objects.create(
        user_rule=rule,
        field=field,
        permission=UserFieldPermission.PermissionChoices.READ
    )
    
    url = reverse(
        "api:database:user_permissions:filtered_view",
        kwargs={"table_id": table.id}
    )
    
    api_client.force_authenticate(user=user)
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    
    response_data = response.json()
    assert response_data["user"]["id"] == user.id
    assert response_data["table"]["id"] == table.id
    assert response_data["user_filters"]["status"] == "published"
    assert field.id in response_data["visible_fields"]
    assert response_data["is_default"] is True


@pytest.mark.django_db 
def test_refresh_user_filtered_view(api_client, data_fixture):
    """Test refreshing user's filtered view"""
    user = data_fixture.create_user(email="user@example.com")
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create user rule
    UserPermissionRule.objects.create(
        table=table,
        user=user,
        role=UserPermissionRule.RoleChoices.COORDINATOR,
        row_filter={"team": "backend"}
    )
    
    # Create existing view
    old_view = UserFilteredView.objects.create(
        table=table,
        user=user,
        name="Old View",
        user_filters={"old": "filter"}
    )
    
    url = reverse(
        "api:database:user_permissions:filtered_view",
        kwargs={"table_id": table.id}
    )
    
    api_client.force_authenticate(user=user)
    response = api_client.post(url)
    
    assert response.status_code == status.HTTP_200_OK
    
    response_data = response.json()
    assert response_data["user_filters"]["team"] == "backend"
    
    # Verify old view was deleted and new one created
    assert not UserFilteredView.objects.filter(id=old_view.id).exists()
    
    new_view = UserFilteredView.objects.get(table=table, user=user)
    assert new_view.user_filters == {"team": "backend"}


@pytest.mark.django_db
def test_list_audit_logs(api_client, data_fixture):
    """Test listing user permission audit logs"""
    admin = data_fixture.create_user(email="admin@example.com")
    user = data_fixture.create_user(email="user@example.com")
    
    workspace = data_fixture.create_workspace(user=admin)
    workspace.users.add(user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # Create some audit logs
    UserPermissionAuditLog.objects.create(
        table=table,
        target_user=user,
        actor_user=admin,
        action=UserPermissionAuditLog.ActionChoices.GRANTED,
        details={"role": "viewer"}
    )
    
    UserPermissionAuditLog.objects.create(
        table=table,
        target_user=user,
        actor_user=admin,
        action=UserPermissionAuditLog.ActionChoices.MODIFIED,
        details={"role": "manager"}
    )
    
    # Admin rule to allow audit access
    UserPermissionRule.objects.create(
        table=table,
        user=admin,
        role=UserPermissionRule.RoleChoices.ADMIN
    )
    
    url = reverse(
        "api:database:user_permissions:audit_logs",
        kwargs={"table_id": table.id}
    )
    
    api_client.force_authenticate(user=admin)
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
    
    # Verify logs are ordered by creation date (newest first)
    logs = response.json()
    assert logs[0]["action"] == "modified"
    assert logs[1]["action"] == "granted"


@pytest.mark.django_db
def test_non_admin_cannot_manage_permissions(api_client, data_fixture):
    """Test that non-admin users cannot manage permissions"""
    user1 = data_fixture.create_user(email="user1@example.com")
    user2 = data_fixture.create_user(email="user2@example.com")
    
    workspace = data_fixture.create_workspace(user=user1)
    workspace.users.add(user2)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_table_for_database(database=database)
    
    # user1 has viewer role (not admin)
    UserPermissionRule.objects.create(
        table=table,
        user=user1,
        role=UserPermissionRule.RoleChoices.VIEWER
    )
    
    url = reverse(
        "api:database:user_permissions:list_create",
        kwargs={"table_id": table.id}
    )
    
    data = {
        "user_id": user2.id,
        "role": "viewer"
    }
    
    api_client.force_authenticate(user=user1)
    response = api_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"] == "ERROR_CANNOT_MANAGE_USER_PERMISSIONS"


@pytest.mark.django_db
def test_table_not_found(api_client, data_fixture):
    """Test API response when table doesn't exist"""
    user = data_fixture.create_user()
    
    url = reverse(
        "api:database:user_permissions:list_create",
        kwargs={"table_id": 99999}
    )
    
    api_client.force_authenticate(user=user)
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"