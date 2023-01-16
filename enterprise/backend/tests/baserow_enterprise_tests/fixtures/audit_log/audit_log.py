from django.shortcuts import reverse

from rest_framework.status import HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_204_NO_CONTENT

from baserow.contrib.database.fields.actions import (
    CreateFieldActionType,
    DeleteFieldActionType,
    UpdateFieldActionType,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.rows.actions import (
    CreateRowActionType,
    DeleteRowActionType,
    UpdateRowActionType,
)
from baserow.contrib.database.table.actions import (
    CreateTableActionType,
    DeleteTableActionType,
    UpdateTableActionType,
)
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.actions import (
    CreateViewActionType,
    DeleteViewActionType,
    UpdateViewActionType,
)
from baserow.contrib.database.views.models import View
from baserow.core.actions import (
    CreateApplicationActionType,
    CreateGroupActionType,
    DeleteApplicationActionType,
    DeleteGroupActionType,
    UpdateApplicationActionType,
    UpdateGroupActionType,
)
from baserow.core.models import Application, Group


def default_group_actions(group=None):

    group_name = group.name if group else "group"

    group_already_exists_actions = [
        {
            "url": lambda: reverse(
                "api:applications:list",
                kwargs={"group_id": Group.objects.get(name=group_name).id},
            ),
            "method": "post",
            "data": {
                "name": "application 1",
                "type": "database",
            },
            "action_type": CreateApplicationActionType,
        },
        {
            "url": lambda: reverse(
                "api:applications:item",
                kwargs={
                    "application_id": Application.objects.get(name="application 1").id
                },
            ),
            "method": "patch",
            "data": {"name": "application"},
            "action_type": UpdateApplicationActionType,
        },
        {
            "url": lambda: reverse(
                "api:database:tables:list",
                kwargs={"database_id": Application.objects.get(name="application").id},
            ),
            "method": "post",
            "data": {"name": "table 1"},
            "action_type": CreateTableActionType,
        },
        {
            "url": lambda: reverse(
                "api:database:tables:item",
                kwargs={"table_id": Table.objects.get(name="table 1").id},
            ),
            "method": "patch",
            "data": {"name": "table"},
            "action_type": UpdateTableActionType,
        },
        {
            "init": lambda _, usr: FieldHandler().create_field(
                usr,
                table=Table.objects.get(name="table"),
                type_name="text",
                name="primary",
            ),
            "url": lambda: reverse(
                "api:database:fields:list",
                kwargs={"table_id": Table.objects.get(name="table").id},
            ),
            "method": "post",
            "data": {"name": "field 1", "type": "text"},
            "action_type": CreateFieldActionType,
        },
        {
            "url": lambda: reverse(
                "api:database:fields:item",
                kwargs={"field_id": Field.objects.get(name="field 1").id},
            ),
            "method": "patch",
            "data": {"name": "field"},
            "action_type": UpdateFieldActionType,
        },
        {
            "url": lambda: reverse(
                "api:database:views:list",
                kwargs={"table_id": Table.objects.get(name="table").id},
            ),
            "method": "post",
            "data": {"name": "view 1", "type": "grid"},
            "action_type": CreateViewActionType,
        },
        {
            "url": lambda: reverse(
                "api:database:views:item",
                kwargs={"view_id": View.objects.get(name="view 1").id},
            ),
            "method": "patch",
            "data": {"name": "view"},
            "action_type": UpdateViewActionType,
        },
        {
            "url": lambda: (
                reverse(
                    "api:database:rows:list",
                    kwargs={"table_id": Table.objects.get(name="table").id},
                )
                + "?user_field_names=true"
            ),
            "method": "post",
            "data": {"primary": "1", "field": "2"},
            "action_type": CreateRowActionType,
        },
        {
            "url": lambda: (
                reverse(
                    "api:database:rows:item",
                    kwargs={
                        "row_id": 1,
                        "table_id": Table.objects.get(name="table").id,
                    },
                )
                + "?user_field_names=true"
            ),
            "method": "patch",
            "data": {"primary": "1", "field": "3"},
            "action_type": UpdateRowActionType,
        },
        {
            "url": lambda: reverse(
                "api:database:rows:item",
                kwargs={"row_id": 1, "table_id": Table.objects.get(name="table").id},
            ),
            "method": "delete",
            "data": None,
            "action_type": DeleteRowActionType,
        },
        {
            "url": lambda: reverse(
                "api:database:fields:item",
                kwargs={"field_id": Field.objects.get(name="field").id},
            ),
            "method": "delete",
            "data": None,
            "action_type": DeleteFieldActionType,
        },
        {
            "url": lambda: reverse(
                "api:database:views:item",
                kwargs={"view_id": View.objects.get(name="view").id},
            ),
            "method": "delete",
            "data": None,
            "action_type": DeleteViewActionType,
        },
        {
            "url": lambda: reverse(
                "api:database:tables:item",
                kwargs={"table_id": Table.objects.get(name="table").id},
            ),
            "method": "delete",
            "data": None,
            "action_type": DeleteTableActionType,
        },
        {
            "url": lambda: reverse(
                "api:applications:item",
                kwargs={
                    "application_id": Application.objects.get(name="application").id
                },
            ),
            "method": "delete",
            "data": None,
            "action_type": DeleteApplicationActionType,
        },
    ]

    if group is None:
        return [
            {
                "url": reverse("api:groups:list"),
                "method": "post",
                "data": {"name": f"{group_name} 1"},
                "action_type": CreateGroupActionType,
            },
            {
                "url": lambda: reverse(
                    "api:groups:item",
                    kwargs={"group_id": Group.objects.get(name=f"{group_name} 1").id},
                ),
                "method": "patch",
                "data": {"name": group_name},
                "action_type": UpdateGroupActionType,
            },
            *group_already_exists_actions,
            {
                "url": lambda: reverse(
                    "api:groups:item",
                    kwargs={"group_id": Group.objects.get(name=group_name).id},
                ),
                "method": "delete",
                "data": None,
                "action_type": DeleteGroupActionType,
            },
        ]

    return group_already_exists_actions


def submit_action_via_api(api_client, action, token):

    if callable(action["url"]):
        url = action["url"]()
    else:
        url = action["url"]

    response = getattr(api_client, action["method"])(
        url, data=action["data"], HTTP_AUTHORIZATION=f"JWT {token}"
    )

    if response.status_code == HTTP_202_ACCEPTED:  # wait for the job to finish
        job_id = response.json()["id"]
        response = api_client.get(
            reverse("api:jobs:item", kwargs={"job_id": job_id}),
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.json()["state"] == "finished"

    assert response.status_code in [HTTP_200_OK, HTTP_204_NO_CONTENT]


class AuditLogFixture:
    def submit_actions_via_api(self, api_client, user=None, actions=None, group=None):
        if user is None:
            user = self.create_user()

        if actions is None:
            actions = default_group_actions(group)

        token = self.generate_token(user)

        for action in actions:
            if "init" in action:
                action["init"](self, user)
            submit_action_via_api(api_client, action, token)

        return actions
