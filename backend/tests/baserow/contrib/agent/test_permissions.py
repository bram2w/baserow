import pytest

from baserow.contrib.agent.operations import ReadAgentSettingsOperationType
from baserow.contrib.agent.service import AgentService
from baserow.core.actions import ExportApplicationsActionType
from baserow.core.handler import CoreHandler
from baserow.core.operations import (
    ReadApplicationOperationType,
    UpdateApplicationOperationType,
)
from baserow.core.service import CoreService


def call(name, user, agent):
    service = AgentService()
    calls = {
        "read agent": lambda: CoreService().get_application(user, agent.id),
        "read settings": lambda: service.get_configuration(user, agent.id),
        "update settings": lambda: service.update_configuration(
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
        ("read agent", [ReadApplicationOperationType]),
        ("read settings", [ReadAgentSettingsOperationType]),
        ("update settings", [UpdateApplicationOperationType]),
        ("export", [ReadAgentSettingsOperationType]),
    ],
)
def test_each_call_checks_its_operation_on_the_agent(
    data_fixture, configured_agent, use_tmp_media_root, mocker, name, operations
):
    user = data_fixture.create_user()
    agent = configured_agent(user=user)
    check = mocker.spy(CoreHandler, "check_permissions")

    call(name, user, agent)

    assert [
        (args[2], kwargs["context"].id) for args, kwargs in check.call_args_list
    ] == [(operation.type, agent.id) for operation in operations]
