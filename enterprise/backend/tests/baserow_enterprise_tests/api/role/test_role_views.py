import json

from django.shortcuts import reverse
from django.test.utils import override_settings

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

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
    group = data_fixture.create_group(
        user=user,
        custom_permissions=[(user2, "VIEWER")],
    )
    database = data_fixture.create_database_application(group=group)

    table = data_fixture.create_database_table(database=database, user=user)

    admin_role = Role.objects.get(uid="ADMIN")
    editor_role = Role.objects.get(uid="EDITOR")
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

    response_json = response.json()

    assert response.status_code == HTTP_200_OK

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
            "role": editor_role.uid,
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    role_assignment_user_2 = RoleAssignmentHandler().get_current_role_assignment(
        user2, group
    )

    assert role_assignment_user_2.role == editor_role
    assert role_assignment_user_2.scope == group

    # Check that we don't create new RoleAssignment for the same scope/subject/group
    response = api_client.post(
        url,
        {
            "scope_id": table.id,
            "scope_type": "database_table",
            "subject_id": user2.id,
            "subject_type": UserSubjectType.type,
            "role": editor_role.uid,
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    role_assignment_user_2 = RoleAssignmentHandler().get_current_role_assignment(
        user2, group, scope=table
    )

    assert role_assignment_user_2.role == editor_role
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

    # Put admin at database level and try to change a sub scope to another role
    response = api_client.post(
        url,
        {
            "scope_id": database.id,
            "scope_type": "database",
            "subject_id": user2.id,
            "subject_type": UserSubjectType.type,
            "role": admin_role.uid,
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        url,
        {
            "scope_id": table.id,
            "scope_type": "database_table",
            "subject_id": user2.id,
            "subject_type": UserSubjectType.type,
            "role": editor_role.uid,
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    response_json = response.json()

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json == {
        "error": "ERROR_CANT_ASSIGN_ROLE_EXCEPTION_TO_ADMIN",
        "detail": "You can't assign a role exception to a scope with ADMIN role.",
    }

    # But we can still change the role at this level
    response = api_client.post(
        url,
        {
            "scope_id": database.id,
            "scope_type": "database",
            "subject_id": user2.id,
            "subject_type": UserSubjectType.type,
            "role": editor_role.uid,
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_200_OK


def test_create_role_assignment_invalid_requests(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2 = data_fixture.create_user()
    user_3 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2])
    group_2 = data_fixture.create_group()
    role = Role.objects.get(uid="ADMIN")

    url = reverse("api:enterprise:role:list", kwargs={"group_id": group.id})

    response = api_client.post(
        url,
        data=json.dumps(
            {
                "scope_id": 9999,
                "scope_type": "group",
                "subject_id": user_2.id,
                "subject_type": UserSubjectType.type,
                "role": role.uid,
            }
        ),
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_SCOPE_DOES_NOT_EXIST"

    response = api_client.post(
        url,
        data=json.dumps(
            {
                "scope_id": group.id,
                "scope_type": "nonsense",
                "subject_id": user_2.id,
                "subject_type": UserSubjectType.type,
                "role": role.uid,
            }
        ),
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_OBJECT_SCOPE_TYPE_DOES_NOT_EXIST"

    response = api_client.post(
        url,
        data=json.dumps(
            {
                "scope_id": group.id,
                "scope_type": "group",
                "subject_id": 99999,
                "subject_type": UserSubjectType.type,
                "role": role.uid,
            }
        ),
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_SUBJECT_DOES_NOT_EXIST"

    response = api_client.post(
        url,
        data=json.dumps(
            {
                "scope_id": group.id,
                "scope_type": "group",
                "subject_id": user_2.id,
                "subject_type": "nonsense",
                "role": role.uid,
            }
        ),
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_SUBJECT_TYPE_DOES_NOT_EXIST"

    response = api_client.post(
        url,
        data=json.dumps(
            {
                "scope_id": group.id,
                "scope_type": "group",
                "subject_id": user_2.id,
                "subject_type": UserSubjectType.type,
                "role": 999999,
            }
        ),
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ROLE_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:enterprise:role:list", kwargs={"group_id": group_2.id}),
        data=json.dumps(
            {
                "scope_id": group_2.id,
                "scope_type": "group",
                "subject_id": user_3.id,
                "subject_type": UserSubjectType.type,
                "role": role.uid,
            }
        ),
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.post(
        reverse("api:enterprise:role:list", kwargs={"group_id": 999999}),
        data=json.dumps(
            {
                "scope_id": group.id,
                "scope_type": "group",
                "subject_id": user_2.id,
                "subject_type": UserSubjectType.type,
                "role": role.uid,
            }
        ),
        content_type="application/json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"


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


@pytest.mark.django_db
def test_batch_assign_role_is_undoable(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2 = data_fixture.create_user()
    user_3 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user_2, user_3])
    role = Role.objects.get(uid="ADMIN")
    session_id = "TEST"

    url = reverse("api:enterprise:role:batch", kwargs={"group_id": group.id})

    initial_role_user_2 = (
        RoleAssignmentHandler().get_current_role_assignment(user_2, group=group).role
    )
    initial_role_user_3 = (
        RoleAssignmentHandler().get_current_role_assignment(user_3, group=group).role
    )

    role_assignments = [
        {
            "scope_id": group.id,
            "scope_type": "group",
            "subject_id": user_2.id,
            "subject_type": UserSubjectType.type,
            "role": role.uid,
        },
        {
            "scope_id": group.id,
            "scope_type": "group",
            "subject_id": user_3.id,
            "subject_type": UserSubjectType.type,
            "role": role.uid,
        },
    ]

    api_client.post(
        url,
        {"items": role_assignments},
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
        HTTP_CLIENTSESSIONID=session_id,
    )

    assert (
        RoleAssignmentHandler().get_current_role_assignment(user_2, group=group).role
        == role
    )
    assert (
        RoleAssignmentHandler().get_current_role_assignment(user_3, group=group).role
        == role
    )

    api_client.patch(
        reverse("api:user:undo"),
        {"scopes": {"root": True, "group": group.id}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_CLIENTSESSIONID=session_id,
    )

    assert (
        RoleAssignmentHandler().get_current_role_assignment(user_2, group=group).role
        == initial_role_user_2
    )

    assert (
        RoleAssignmentHandler().get_current_role_assignment(user_3, group=group).role
        == initial_role_user_3
    )
