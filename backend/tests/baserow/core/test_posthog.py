from unittest.mock import patch

from django.test.utils import override_settings

import pytest

from baserow.core.posthog import capture_event


@pytest.mark.django_db
@override_settings(POSTHOG_ENABLED=False)
@patch("baserow.core.posthog.posthog")
def test_not_capture_event_if_not_enabled(mock_posthog, data_fixture):
    user = data_fixture.create_user()
    capture_event(user, "test", {})
    mock_posthog.capture.assert_not_called()


@pytest.mark.django_db
@override_settings(POSTHOG_ENABLED=True)
@patch("baserow.core.posthog.posthog")
def test_capture_event_if_enabled(mock_posthog, data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace()
    capture_event(user, "test", {}, session="session", workspace=workspace)
    mock_posthog.capture.assert_called_once_with(
        distinct_id=user.id,
        event="test",
        properties={
            "user_email": user.email,
            "user_session": "session",
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
        },
    )
