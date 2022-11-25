import json

from django.shortcuts import reverse
from django.test.utils import override_settings

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT

from baserow.core.subjects import UserSubjectType
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role, RoleAssignment


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise):
    pass


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_role_assignment(
    api_client, data_fixture, enterprise_data_fixture, synced_roles
):
    user, token = data_fixture.create_user_and_token()
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user2])
    database = data_fixture.create_database_application(group=group)

    table = data_fixture.create_database_table(user=user, database=database)

    admin_role = Role.objects.get(uid="ADMIN")
    builder_role = Role.objects.get(uid="BUILDER")

    assert len(RoleAssignment.objects.all()) == 0

    url = reverse("api:enterprise:role:list", kwargs={"group_id": group.id})

    # Can add a first roleAssignment
    response = api_client.post(
        url,
        {
            "scope_id": table.id,
            "scope_type": "database_table",
            "subject_id": user2.id,
            "subject_type": UserSubjectType.type,
            "role": builder_role.uid,
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    role_assignment_user_2 = RoleAssignmentHandler().get_current_role_assignment(
        user2, group, scope=table
    )

    assert role_assignment_user_2.scope == table
    assert role_assignment_user_2.subject == user2
    assert role_assignment_user_2.role == builder_role
    assert role_assignment_user_2.group == group

    assert response_json == {
        "id": role_assignment_user_2.id,
        "role": builder_role.uid,
        "scope_id": table.id,
        "scope_type": "database_table",
        "subject_id": user2.id,
        "subject_type": UserSubjectType.type,
        "subject": {
            "email": user2.email,
            "first_name": user2.first_name,
            "id": user2.id,
            "username": user2.username,
        },
    }

    # Can we create another roleAssignment
    response = api_client.post(
        url,
        {
            "scope_id": group.id,
            "scope_type": "group",
            "subject_id": user2.id,
            "subject_type": UserSubjectType.type,
            "role": admin_role.uid,
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    role_assignment_user_2 = RoleAssignmentHandler().get_current_role_assignment(
        user2, group
    )

    assert role_assignment_user_2.role == admin_role
    assert role_assignment_user_2.scope == group

    # Check that we don't create new RoleAssignment for the same scope/subject/group
    response = api_client.post(
        url,
        {
            "scope_id": table.id,
            "scope_type": "database_table",
            "subject_id": user2.id,
            "subject_type": UserSubjectType.type,
            "role": admin_role.uid,
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    role_assignment_user_2 = RoleAssignmentHandler().get_current_role_assignment(
        user2, group, scope=table
    )

    assert role_assignment_user_2.role == admin_role
    assert role_assignment_user_2.scope == table

    # Can we remove a role
    response = api_client.post(
        url,
        data=json.dumps(
            {
                "scope_id": table.id,
                "scope_type": "database_table",
                "subject_id": user2.id,
                "subject_type": UserSubjectType.type,
                "role": None,
            }
        ),
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    role_assignment_user_2 = RoleAssignmentHandler().get_current_role_assignment(
        user2, group, scope=table
    )

    assert role_assignment_user_2 is None


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_get_role_assignments_group_level(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])

    url = reverse("api:enterprise:role:list", kwargs={"group_id": group.id})

    response = api_client.get(
        url,
        {
            "scope_id": group.id,
            "scope_type": "group",
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 2
    assert response_json == [
        {
            "id": None,
            "role": "ADMIN",
            "scope_id": group.id,
            "scope_type": "group",
            "subject_id": user.id,
            "subject_type": "auth.User",
            "subject": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "email": user.email,
            },
        },
        {
            "id": None,
            "role": "BUILDER",
            "scope_id": group.id,
            "scope_type": "group",
            "subject_id": user_2.id,
            "subject_type": "auth.User",
            "subject": {
                "id": user_2.id,
                "username": user_2.username,
                "first_name": user_2.first_name,
                "email": user_2.email,
            },
        },
    ]


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_get_role_assignments_application_level(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    database = data_fixture.create_database_application(group=group)

    admin_role = Role.objects.get(uid="ADMIN")

    role_assignment = RoleAssignmentHandler().assign_role(
        user_2, group, role=admin_role, scope=database
    )

    url = reverse("api:enterprise:role:list", kwargs={"group_id": group.id})

    response = api_client.get(
        url,
        {
            "scope_id": database.id,
            "scope_type": "database",
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 1
    assert response_json == [
        {
            "id": role_assignment.id,
            "role": admin_role.uid,
            "scope_id": database.id,
            "scope_type": "database",
            "subject_id": user_2.id,
            "subject_type": "auth.User",
            "subject": {
                "id": user_2.id,
                "username": user_2.username,
                "first_name": user_2.first_name,
                "email": user_2.email,
            },
        },
    ]


@pytest.mark.django_db
def test_get_role_assignments_table_level(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    user_2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)

    admin_role = Role.objects.get(uid="ADMIN")

    role_assignment = RoleAssignmentHandler().assign_role(
        user_2, group, role=admin_role, scope=table
    )

    url = reverse("api:enterprise:role:list", kwargs={"group_id": group.id})

    response = api_client.get(
        url,
        {
            "scope_id": table.id,
            "scope_type": "database_table",
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 1
    assert response_json == [
        {
            "id": role_assignment.id,
            "role": admin_role.uid,
            "scope_id": table.id,
            "scope_type": "database_table",
            "subject_id": user_2.id,
            "subject_type": "auth.User",
            "subject": {
                "id": user_2.id,
                "username": user_2.username,
                "first_name": user_2.first_name,
                "email": user_2.email,
            },
        },
    ]


@pytest.mark.django_db
def test_batch_assign_role(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user2])
    database = data_fixture.create_database_application(group=group)

    table = data_fixture.create_database_table(user=user, database=database)

    builder_role = Role.objects.get(uid="BUILDER")

    assert len(RoleAssignment.objects.all()) == 0

    url = reverse("api:enterprise:role:batch", kwargs={"group_id": group.id})

    # Can add a first roleAssignment
    response = api_client.post(
        url,
        {
            "items": [
                {
                    "scope_id": table.id,
                    "scope_type": "database_table",
                    "subject_id": user2.id,
                    "subject_type": UserSubjectType.type,
                    "role": builder_role.uid,
                },
            ]
        },
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    role_assignment_user_2 = RoleAssignmentHandler().get_current_role_assignment(
        user2, group, scope=table
    )

    assert role_assignment_user_2.scope == table
    assert role_assignment_user_2.subject == user2
    assert role_assignment_user_2.role == builder_role
    assert role_assignment_user_2.group == group

    assert response_json == [
        {
            "id": role_assignment_user_2.id,
            "role": builder_role.uid,
            "scope_id": table.id,
            "scope_type": "database_table",
            "subject_id": user2.id,
            "subject_type": UserSubjectType.type,
            "subject": {
                "email": user2.email,
                "first_name": user2.first_name,
                "id": user2.id,
                "username": user2.username,
            },
        }
    ]


@pytest.mark.django_db
def test_batch_assign_role_duplicates(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user2])
    database = data_fixture.create_database_application(group=group)

    table = data_fixture.create_database_table(user=user, database=database)

    builder_role = Role.objects.get(uid="BUILDER")

    url = reverse("api:enterprise:role:batch", kwargs={"group_id": group.id})

    role_assignment = {
        "scope_id": table.id,
        "scope_type": "database_table",
        "subject_id": user2.id,
        "subject_type": UserSubjectType.type,
        "role": builder_role.uid,
    }

    # Can add a first roleAssignment
    response = api_client.post(
        url,
        {"items": [role_assignment, role_assignment]},
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "ERROR_DUPLICATE_ROLE_ASSIGNMENTS"
    assert (
        response.json()["detail"]
        == "The list of role assignments includes duplicates at indexes: [0]"
    )
