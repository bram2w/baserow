from django.db import IntegrityError

import pytest


@pytest.mark.once_per_day_in_ci
def test_0082_remove_duplicate_workspace_invitation_forwards(
    migrator, teardown_table_metadata
):
    migrate_from = [
        ("core", "0081_usersource_uid"),
    ]
    migrate_to = [
        (
            "core",
            "0083_alter_workspaceinvitation_unique_together",
        )
    ]

    old_state = migrator.migrate(migrate_from)
    User = old_state.apps.get_model("auth", "User")
    sender = User.objects.create(username="sender")
    Workspace = old_state.apps.get_model("core", "Workspace")
    Workspace.objects.bulk_create(
        [
            Workspace(id=1, name="wp1"),
            Workspace(id=2, name="wp2"),
        ]
    )

    WorkspaceInvitation = old_state.apps.get_model("core", "WorkspaceInvitation")

    WorkspaceInvitation.objects.bulk_create(
        [
            WorkspaceInvitation(
                id=1, email="a@baserow.io", workspace_id=1, invited_by_id=sender.id
            ),
            WorkspaceInvitation(
                id=2, email="a@baserow.io", workspace_id=1, invited_by_id=sender.id
            ),
            WorkspaceInvitation(
                id=3, email="a@baserow.io", workspace_id=2, invited_by_id=sender.id
            ),
            WorkspaceInvitation(
                id=4, email="b@baserow.io", workspace_id=1, invited_by_id=sender.id
            ),
            WorkspaceInvitation(
                id=5, email="b@baserow.io", workspace_id=2, invited_by_id=sender.id
            ),
            WorkspaceInvitation(
                id=6, email="b@baserow.io", workspace_id=2, invited_by_id=sender.id
            ),
            WorkspaceInvitation(
                id=7, email="c@baserow.io", workspace_id=2, invited_by_id=sender.id
            ),
            WorkspaceInvitation(
                id=8, email="c@baserow.io", workspace_id=2, invited_by_id=sender.id
            ),
            WorkspaceInvitation(
                id=9, email="c@baserow.io", workspace_id=2, invited_by_id=sender.id
            ),
            WorkspaceInvitation(
                id=10, email="c@baserow.io", workspace_id=2, invited_by_id=sender.id
            ),
        ]
    )

    assert WorkspaceInvitation.objects.count() == 10

    new_state = migrator.migrate(migrate_to)
    NewWorkspaceInvitation = new_state.apps.get_model("core", "WorkspaceInvitation")

    assert NewWorkspaceInvitation.objects.count() == 5
    remaining_ids = list(
        NewWorkspaceInvitation.objects.values_list("id", flat=True).order_by("id")
    )
    assert remaining_ids == [2, 3, 4, 6, 10]

    # And now it's not possible to create a new duplicate
    with pytest.raises(IntegrityError):
        NewWorkspaceInvitation.objects.create(
            email="a@baserow.io", workspace_id=1, invited_by_id=sender.id
        ),
