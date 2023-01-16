import dataclasses
import json
from datetime import datetime

from django.shortcuts import reverse
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import pytest
from freezegun import freeze_time
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)

from baserow.core.action.registries import (
    ActionScopeStr,
    ActionType,
    ActionTypeDescription,
    action_type_registry,
)
from baserow_enterprise.audit_log.models import AuditLogEntry


@pytest.mark.django_db()
@override_settings(DEBUG=True)
def test_audit_log_entries_can_be_filtered(
    api_client, enterprise_data_fixture, synced_roles
):

    # create the admin token to access the audit log data
    (
        admin_user,
        admin_token,
    ) = enterprise_data_fixture.create_enterprise_admin_user_and_token()
    user, unauthorized_token = enterprise_data_fixture.create_user_and_token()

    count = 10
    users = [admin_user, user]
    groups = []
    action_types = action_type_registry.get_types()

    # insert count * len(action_types) entries
    for __ in range(count):
        user = enterprise_data_fixture.create_user()
        group = enterprise_data_fixture.create_group(user=user)
        actions = enterprise_data_fixture.submit_actions_via_api(
            api_client, user=user, group=group
        )

        users.append(user)
        groups.append(group)

    # ensure only the admin can access the audit log
    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:users"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {unauthorized_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:groups"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {unauthorized_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:action_types"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {unauthorized_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {unauthorized_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    # check filters return expected values
    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:users"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": len(users),
        "next": None,
        "previous": None,
        "results": [
            {"id": user.id, "value": user.email}
            for user in sorted(users, key=lambda u: u.email)
        ],
    }

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:groups"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": len(groups),
        "next": None,
        "previous": None,
        "results": [
            {"id": group.id, "value": group.name}
            for group in sorted(groups, key=lambda g: g.name)
        ],
    }

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:action_types"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": len(action_types),
        "next": None,
        "previous": None,
        "results": sorted(
            [
                {
                    "id": action_type,
                    "value": action_type_registry.get(
                        action_type
                    ).get_short_description(),
                }
                for action_type in action_types
            ],
            key=lambda t: t["value"],
        ),
    }
    total_count = count * len(actions)

    # check all the audit log entries are returned
    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == total_count
    assert (
        response_json["next"]
        == "http://testserver"
        + reverse("api:enterprise:admin:audit_log:list")
        + "?page=2"
    )
    assert response_json["previous"] is None

    last_timestamp = timezone.now()
    entries = response_json["results"]
    i, entry_count = 0, len(entries)

    def render_user(user):
        return f"{user.email} ({user.id})"

    def render_group(group):
        return f"{group.name} ({group.id})"

    filter_timestamp, filtered_count = None, 50

    with pytest.raises(StopIteration):
        for j, user in enumerate(users[::-1]):
            group = groups[::-1][j]
            for action in actions[::-1]:
                entry = entries[i]
                action_type_filter = action["action_type"].type
                assert entry["action_type"] == action_type_filter, [
                    e["action_type"] for e in response_json["results"][:5]
                ]
                short_description = action_type_registry.get(
                    action_type_filter
                ).get_short_description()
                assert entry["type"] == short_description
                assert entry["description"]
                assert entry["user"] == render_user(user)
                assert entry["group"] == render_group(group)
                # check that the timestamp is in the correct order
                tstamp = datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%S.%f%z")
                assert tstamp <= last_timestamp
                last_timestamp = tstamp
                i += 1
                if i == filtered_count:
                    filter_timestamp = tstamp
                if i >= entry_count:
                    assert i == 100
                    raise StopIteration

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list")
        + f"?filters=user_id={users[0].id}",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": {"filters": [{"code": "invalid", "error": "Invalid filters JSON."}]},
        "error": "ERROR_QUERY_PARAMETER_VALIDATION",
    }

    # ensure filters work as expected and return the correct number of entries
    def encode_filters(**kwargs):
        return "?filters=" + json.dumps(kwargs)

    admin_without_entries = users[0]
    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list")
        + encode_filters(user_id=admin_without_entries.id),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    # the admin user did not perform any actions
    assert response_json["count"] == 0

    user_with_actions = users[-1]
    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list")
        + encode_filters(user_id=user_with_actions.id),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == len(actions)
    assert response_json["next"] is None
    assert response_json["previous"] is None
    entries = response_json["results"]
    for entry in entries:
        assert entry["user"] == render_user(user_with_actions)

    group_filter = groups[0]
    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list")
        + encode_filters(group_id=group_filter.id),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == len(actions)
    assert response_json["next"] is None
    assert response_json["previous"] is None
    entries = response_json["results"]
    for entry in entries:
        assert entry["group"] == render_group(group_filter)

    users_with_actions = users[2:]
    action_type_filter = actions[0]["action_type"].type
    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list")
        + encode_filters(action_type=action_type_filter),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == len(groups)
    assert response_json["next"] is None
    assert response_json["previous"] is None
    assert [e["user"] for e in response_json["results"]] == [
        render_user(u) for u in users_with_actions[::-1]
    ]
    assert [e["group"] for e in response_json["results"]] == [
        render_group(g) for g in groups[::-1]
    ]

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list")
        + encode_filters(
            from_timestamp=filter_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == filtered_count

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list")
        + encode_filters(
            to_timestamp=filter_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")
        ),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == total_count - filtered_count + 1


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
def test_audit_log_can_start_export_job_from_api(
    api_client, enterprise_data_fixture, synced_roles
):
    user = enterprise_data_fixture.create_user()
    group = enterprise_data_fixture.create_group()
    enterprise_data_fixture.submit_actions_via_api(api_client, user=user)

    _, admin_token = enterprise_data_fixture.create_enterprise_admin_user_and_token()

    csv_settings = {
        "csv_column_separator": ",",
        "csv_first_row_header": True,
        "export_charset": "utf-8",
    }

    with freeze_time("2023-01-01 12:00"):
        response = api_client.post(
            reverse("api:enterprise:admin:audit_log:export"),
            data=csv_settings,
            format="json",
            HTTP_AUTHORIZATION=f"JWT {admin_token}",
        )
    assert response.status_code == HTTP_202_ACCEPTED, response.json()
    job = response.json()
    assert job["id"] is not None
    assert job["state"] == "pending"
    assert job["type"] == "audit_log_export"

    response = api_client.get(
        reverse(
            "api:jobs:item",
            kwargs={"job_id": job["id"]},
        ),
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    job = response.json()
    assert job["state"] == "finished"
    assert job["type"] == "audit_log_export"
    for key, value in csv_settings.items():
        assert job[key] == value
    for key in [
        "filter_user_id",
        "filter_group_id",
        "filter_action_type",
        "filter_from_timestamp",
        "filter_to_timestamp",
    ]:
        assert job[key] is None
    assert job["exported_file_name"].endswith(".csv")
    assert job["url"].startswith("http://localhost:8000/media/export_files/")
    assert job["created_on"] == "2023-01-01T12:00:00Z"

    csv_settings = {
        "csv_column_separator": "|",
        "csv_first_row_header": False,
        "export_charset": "utf-8",
    }
    filters = {
        "filter_user_id": user.id,
        "filter_group_id": group.id,
        "filter_action_type": "application_created",
        "filter_from_timestamp": "2023-01-01T00:00:00Z",
        "filter_to_timestamp": "2023-01-03T00:00:00Z",
    }

    with freeze_time("2023-01-02 12:00"):
        response = api_client.post(
            reverse("api:enterprise:admin:audit_log:export"),
            data={**csv_settings, **filters},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {admin_token}",
        )
    assert response.status_code == HTTP_202_ACCEPTED, response.json()
    job = response.json()
    assert job["id"] is not None
    assert job["state"] == "pending"
    assert job["type"] == "audit_log_export"

    response = api_client.get(
        reverse(
            "api:jobs:item",
            kwargs={"job_id": job["id"]},
        ),
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_200_OK
    job = response.json()
    assert job["state"] == "finished"
    assert job["type"] == "audit_log_export"
    for key, value in csv_settings.items():
        assert job[key] == value
    for key in [
        "filter_user_id",
        "filter_group_id",
        "filter_action_type",
        "filter_from_timestamp",
        "filter_to_timestamp",
    ]:
        assert job[key] == filters[key]
    assert job["exported_file_name"].endswith(".csv")
    assert job["url"].startswith("http://localhost:8000/media/export_files/")
    assert job["created_on"] == "2023-01-02T12:00:00Z"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_log_entries_still_work_correctly_if_the_action_type_is_removed(
    api_client, enterprise_data_fixture, synced_roles
):
    class TemporaryActionType(ActionType):
        type = "temporary"
        description = ActionTypeDescription(
            short=_("Temporary action"),
            long=_("This is a temporary action with value: %(value)s."),
        )

        @dataclasses.dataclass
        class Params:
            value: str

        @classmethod
        def do(cls, user, value):
            return cls.register_action(user, cls.Params(value), cls.scope())

        @classmethod
        def scope(cls, *args, **kwargs) -> ActionScopeStr:
            return "test"

    admin, token = enterprise_data_fixture.create_enterprise_admin_user_and_token()

    assert AuditLogEntry.objects.count() == 0

    action_type_registry.register(TemporaryActionType())
    with freeze_time("2023-01-01 12:00"):
        TemporaryActionType.do(admin, "test")
    assert AuditLogEntry.objects.count() == 1

    entry = AuditLogEntry.objects.first()
    assert entry.action_type == TemporaryActionType.type
    assert entry.original_action_long_descr == TemporaryActionType.description.long
    assert entry.original_action_short_descr == TemporaryActionType.description.short

    action_type_registry.unregister(TemporaryActionType.type)

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 1
    entry = response_json["results"][0]
    expected_data = {
        "action_type": "temporary",
        "description": "This is a temporary action with value: test.",
        "group": "",
        "ip_address": None,
        "timestamp": "2023-01-01T12:00:00Z",
        "type": "Temporary action",
        "user": f"{admin.email} ({admin.id})",
    }
    for key, value in expected_data.items():
        assert entry[key] == value

    # we can also change the action parameters and everything still works
    class TemporaryActionTypeV2(ActionType):
        type = "temporary"
        description = ActionTypeDescription(
            short=_("Temporary action"),
            long=_("This is a temporary action with value: %(value)s and %(uid)s."),
        )

        @dataclasses.dataclass
        class Params:
            value: str
            uid: int

        @classmethod
        def do(cls, user, value, uid):
            return cls.register_action(user, cls.Params(value, uid), cls.scope())

        @classmethod
        def scope(cls, *args, **kwargs) -> ActionScopeStr:
            return "test"

    action_type_registry.register(TemporaryActionTypeV2())

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 1
    entry = response_json["results"][0]

    # the previous entry now use the new description, leaving the
    # placeholder for the new missing parameter
    expected_data = {
        "action_type": "temporary",
        "description": "This is a temporary action with value: test and %(uid)s.",
        "group": "",
        "ip_address": None,
        "timestamp": "2023-01-01T12:00:00Z",
        "type": "Temporary action",
        "user": f"{admin.email} ({admin.id})",
    }
    for key, value in expected_data.items():
        assert entry[key] == value

    # if we now perform a new action, the new description will contain the new uid value
    with freeze_time("2023-01-01 12:01"):
        TemporaryActionTypeV2.do(admin, "test", 42)

    assert AuditLogEntry.objects.count() == 2

    response = api_client.get(
        reverse("api:enterprise:admin:audit_log:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 2
    expected_data = [
        {
            "action_type": "temporary",
            "description": "This is a temporary action with value: test and 42.",
            "group": "",
            "ip_address": None,
            "timestamp": "2023-01-01T12:01:00Z",
            "type": "Temporary action",
            "user": f"{admin.email} ({admin.id})",
        },
        {
            "action_type": "temporary",
            "description": "This is a temporary action with value: test and %(uid)s.",
            "group": "",
            "ip_address": None,
            "timestamp": "2023-01-01T12:00:00Z",
            "type": "Temporary action",
            "user": f"{admin.email} ({admin.id})",
        },
    ]
    for entry, expected_data in zip(response_json["results"], expected_data):
        for key, value in expected_data.items():
            assert entry[key] == value
