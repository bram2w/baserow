from datetime import datetime, timedelta, timezone

import pytest

from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View
from baserow.core.user.handler import UserHandler


@pytest.mark.django_db(transaction=True)
@pytest.mark.view_ownership
def test_remove_unused_personal_views(
    data_fixture, alternative_per_workspace_license_service
):
    workspace = data_fixture.create_workspace(name="Workspace 1")
    user = data_fixture.create_user(workspace=workspace)
    user2 = data_fixture.create_user(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_workspace_license_service.restrict_user_premium_to(
        user, workspace.id
    )
    view = handler.create_view(
        user=user,
        table=table,
        type_name="form",
        name="Form personal",
        ownership_type="personal",
    )
    view2 = handler.create_view(
        user=user,
        table=table,
        type_name="form",
        name="Form collaborative",
        ownership_type="collaborative",
    )

    views = View.objects.filter(table=table)
    assert len(views) == 2

    user.profile.to_be_deleted = True
    user.profile.save()
    user.last_login = datetime.now(tz=timezone.utc) - timedelta(weeks=100)
    user.save()

    UserHandler().delete_expired_users_and_related_workspaces_if_last_admin(
        grace_delay=timedelta(days=1)
    )

    views = View.objects.filter(table=table)
    assert len(views) == 1
    assert views[0].name == "Form collaborative"
