from django.urls import reverse

import pytest

from baserow.contrib.agent.operations import ReadAgentSettingsOperationType
from baserow.core.handler import CoreHandler
from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role

CONFIGURE = {ReadAgentSettingsOperationType.type}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role_uid,granted",
    [
        ("VIEWER", set()),
        ("COMMENTER", set()),
        ("EDITOR", set()),
        ("BUILDER", CONFIGURE),
        ("ADMIN", CONFIGURE),
    ],
)
def test_default_roles_grant_agent_operations(
    enterprise_data_fixture, enable_enterprise, synced_roles, role_uid, granted
):
    member = enterprise_data_fixture.create_user()
    workspace = enterprise_data_fixture.create_workspace(
        user=enterprise_data_fixture.create_user(), members=[member]
    )
    agent = enterprise_data_fixture.create_agent_application(workspace=workspace)
    RoleAssignmentHandler().assign_role(
        member, workspace, Role.objects.get(uid=role_uid)
    )

    allowed = {
        operation
        for operation in CONFIGURE
        if CoreHandler().check_permissions(
            member,
            operation,
            workspace=workspace,
            context=agent,
            raise_permission_exceptions=False,
        )
    }

    assert allowed == granted


@pytest.mark.django_db
@pytest.mark.parametrize("can_read_agent", [True, False])
def test_agent_readiness_follows_application_access_without_settings_access(
    enterprise_data_fixture,
    enable_enterprise,
    synced_roles,
    api_client,
    can_read_agent,
):
    member, token = enterprise_data_fixture.create_user_and_token()
    workspace = enterprise_data_fixture.create_workspace(
        user=enterprise_data_fixture.create_user(), members=[member]
    )
    agent = enterprise_data_fixture.create_agent_application(
        workspace=workspace,
        instructions="PRIVATE INSTRUCTIONS",
        provider_type="openai",
        model_identifier="unavailable-model",
    )
    RoleAssignmentHandler().assign_role(
        member, workspace, Role.objects.get(uid="VIEWER")
    )
    if not can_read_agent:
        RoleAssignmentHandler().assign_role(
            member, workspace, Role.objects.get(uid="NO_ACCESS"), scope=agent
        )
    api_client.credentials(HTTP_AUTHORIZATION=f"JWT {token}")

    for url in (
        reverse("api:agent:item", kwargs={"agent_id": agent.id}),
        reverse("api:applications:item", kwargs={"application_id": agent.id}),
    ):
        response = api_client.get(url)

        assert response.status_code == (200 if can_read_agent else 401)
        payload = response.json()
        if can_read_agent:
            assert payload["readiness"] == "unavailable"
            assert not {
                "instructions",
                "provider_type",
                "model_identifier",
                "errors",
                "state",
            }.intersection(payload)
        else:
            assert payload["error"] == "PERMISSION_DENIED"
            assert "readiness" not in payload

    for url in (
        reverse("api:applications:list", kwargs={"workspace_id": workspace.id}),
        reverse("api:applications:list"),
    ):
        response = api_client.get(url)

        assert response.status_code == 200
        if can_read_agent:
            [payload] = response.json()
            assert payload["id"] == agent.id
            assert payload["readiness"] == "unavailable"
        else:
            assert response.json() == []

    response = api_client.get(
        reverse("api:agent:configuration", kwargs={"agent_id": agent.id})
    )
    assert response.status_code == 401
    assert response.json()["error"] == "PERMISSION_DENIED"
