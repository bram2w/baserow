import pytest

from baserow.contrib.agent.operations import ReadAgentConfigurationOperationType
from baserow.contrib.agent.service import AgentService
from baserow.core.actions import ExportApplicationsActionType
from baserow.core.handler import CoreHandler
from baserow.core.operations import UpdateApplicationOperationType


def call(name, user, agent):
    service = AgentService()
    calls = {
        "read configuration": lambda: service.get_configuration(user, agent.id),
        "update configuration": lambda: service.update_configuration(
            user, agent.id, instructions="Changed"
        ),
        "export": lambda: ExportApplicationsActionType.do(
            user, agent.workspace, [agent]
        ),
    }
    return calls[name]()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name,operations",
    [
        ("read configuration", [ReadAgentConfigurationOperationType]),
        (
            "update configuration",
            [UpdateApplicationOperationType, ReadAgentConfigurationOperationType],
        ),
        ("export", [ReadAgentConfigurationOperationType]),
    ],
)
def test_each_call_checks_its_operation_on_the_agent(
    data_fixture, configured_agent, use_tmp_media_root, mocker, name, operations
):
    user = data_fixture.create_user()
    agent = configured_agent(user=user)
    check = mocker.spy(CoreHandler, "check_multiple_permissions")

    call(name, user, agent)

    assert [
        (permission.operation_name, permission.context.id)
        for args, _ in check.call_args_list
        for permission in args[1]
    ] == [(operation.type, agent.id) for operation in operations]
