# noinspection PyPep8Naming
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

migrate_from = [("core", "0018_trashentry_names")]
migrate_to = [("core", "0019_trashentry_extra_description_to_names")]


# noinspection PyPep8Naming
@pytest.mark.django_db(transaction=True)
def test_extra_description_to_names_conversion(data_fixture, reset_schema_after_module):
    old_state = migrate(migrate_from)

    Group = old_state.apps.get_model("core", "Group")
    group = Group.objects.create(name="Group")

    TrashEntry = old_state.apps.get_model("core", "TrashEntry")
    TrashEntry.objects.create(extra_description="", trash_item_id=1, group_id=group.id)
    TrashEntry.objects.create(
        extra_description="Test", trash_item_id=2, group_id=group.id
    )
    TrashEntry.objects.create(
        extra_description="Something,test", trash_item_id=3, group_id=group.id
    )
    TrashEntry.objects.create(
        extra_description=None, trash_item_id=4, group_id=group.id
    )
    assert TrashEntry.objects.all().count() == 4

    new_state = migrate(migrate_to)

    MigrationTrashEntry = new_state.apps.get_model("core", "TrashEntry")
    entries = list(MigrationTrashEntry.objects.all().order_by("id"))
    assert entries[0].extra_description == ""
    assert entries[0].names == []
    assert entries[1].extra_description == "Test"
    assert entries[1].names == ["Test"]
    assert entries[2].extra_description == "Something,test"
    assert entries[2].names == ["Something,test"]
    assert entries[3].extra_description is None
    assert entries[3].names is None


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state
