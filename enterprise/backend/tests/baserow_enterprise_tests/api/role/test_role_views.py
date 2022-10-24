from django.shortcuts import reverse
from django.test.utils import override_settings

import pytest
from baserow_enterprise.role.handler import USER_TYPE
from baserow_enterprise.role.models import Role, RoleAssignment
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_create_role_assignment(api_client, data_fixture, enterprise_data_fixture):
    user, token = data_fixture.create_user_and_token()
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)

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

    role_assignments = list(RoleAssignment.objects.all())

    assert len(role_assignments) == 1

    assert role_assignments[0].scope == table
    assert role_assignments[0].subject == user2
    assert role_assignments[0].role == builder_role
    assert role_assignments[0].group == group

    assert response_json == {
        "id": role_assignments[0].id,
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

    role_assignments = list(RoleAssignment.objects.all())

    assert len(role_assignments) == 2

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

    role_assignments = list(RoleAssignment.objects.all())
    assert len(role_assignments) == 2

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

    role_assignments = list(RoleAssignment.objects.all())
    assert len(role_assignments) == 1
