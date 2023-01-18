from django.test.utils import override_settings
from django.utils import timezone

import pytest

from baserow_enterprise.audit_log.handler import AuditLogHandler
from baserow_enterprise.audit_log.models import AuditLogEntry


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
def test_actions_are_not_inserted_as_audit_log_entries_without_enterprise(
    api_client, enterprise_data_fixture
):

    user = enterprise_data_fixture.create_user()
    actions = enterprise_data_fixture.submit_actions_via_api(api_client, user)
    assert len(actions) > 0
    assert AuditLogEntry.objects.count() == 0


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
def test_actions_are_inserted_as_audit_log_entries_with_enterprise(
    api_client, enterprise_data_fixture, synced_roles
):
    enterprise_data_fixture.enable_enterprise()

    user = enterprise_data_fixture.create_user()
    actions = enterprise_data_fixture.submit_actions_via_api(api_client, user)
    assert len(actions) > 0

    # the entries are sorted in reverse order
    delete_older_than, delete_last = None, 10
    for i, entry in enumerate(AuditLogEntry.objects.all(), start=1):
        action = actions[len(actions) - i]
        assert entry.action_type == action["action_type"].type, (entry, action)
        assert entry.user_id == user.id
        assert entry.user_email == user.email
        assert (
            entry.original_action_short_descr == action["action_type"].description.short
        )
        assert (
            entry.original_action_long_descr == action["action_type"].description.long
        )
        assert (
            entry.original_action_context_descr
            == action["action_type"].description.context
        )
        # ensure the original description can be formatted correctly
        assert entry.original_action_long_descr % entry.action_params
        if i == delete_last:
            delete_older_than = entry.action_timestamp

    # ensure the older entries are deleted correctly
    AuditLogHandler.delete_entries_older_than(delete_older_than)
    assert AuditLogEntry.objects.count() == delete_last

    AuditLogHandler.delete_entries_older_than(timezone.now())
    assert AuditLogEntry.objects.count() == 0
