from django.shortcuts import reverse
from django.test.utils import override_settings

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT

from baserow_enterprise.role.handler import USER_TYPE, RoleAssignmentHandler
from baserow_enterprise.role.models import Role, RoleAssignment


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_role_assignment(
    api_client, data_fixture, enterprise_data_fixture, synced_roles
):
    user, token = data_fixture.create_user_and_token()
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user, members=[user2])

    table = data_fixture.create_database_table(user=user)

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
            "subject_type": USER_TYPE,
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
        "subject_type": USER_TYPE,
    }

    # Can we create another roleAssignment
    response = api_client.post(
        url,
        {
            "scope_id": group.id,
            "scope_type": "group",
            "subject_id": user2.id,
            "subject_type": USER_TYPE,
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
            "subject_type": USER_TYPE,
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
        {
            "scope_id": table.id,
            "scope_type": "database_table",
            "subject_id": user2.id,
            "subject_type": USER_TYPE,
        },
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    role_assignment_user_2 = RoleAssignmentHandler().get_current_role_assignment(
        user2, group, scope=table
    )

    assert role_assignment_user_2 is None
