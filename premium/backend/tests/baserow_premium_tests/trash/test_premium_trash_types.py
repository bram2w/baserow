import pytest

from baserow.contrib.database.views.handler import ViewHandler
from baserow.core.exceptions import PermissionDenied
from baserow.core.trash.handler import TrashHandler


@pytest.mark.django_db
@pytest.mark.view_ownership
def test_trash_restore_view(
    data_fixture, premium_data_fixture, alternative_per_workspace_license_service
):
    workspace = data_fixture.create_workspace(name="Group 1")
    user = premium_data_fixture.create_user(workspace=workspace)
    user2 = premium_data_fixture.create_user(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(user=user, database=database)
    handler = ViewHandler()
    alternative_per_workspace_license_service.restrict_user_premium_to(
        user, workspace.id
    )
    alternative_per_workspace_license_service.restrict_user_premium_to(
        user2, workspace.id
    )
    view = handler.create_view(
        user=user,
        table=table,
        type_name="grid",
        name="Test grid",
        ownership_type="personal",
    )

    TrashHandler.trash(user, database.workspace, database, view)
    view.refresh_from_db()

    assert view.trashed is True

    with pytest.raises(PermissionDenied):
        TrashHandler.restore_item(user2, "view", view.id)

    TrashHandler.restore_item(user, "view", view.id)
    view.refresh_from_db()

    assert view.trashed is False
