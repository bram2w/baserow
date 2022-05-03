# noinspection PyPep8Naming
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.contrib.contenttypes.models import ContentType


# noinspection PyPep8Naming
@pytest.mark.django_db(transaction=True)
def test_forwards_migration(data_fixture, reset_schema_after_module):
    migrate_from = [("database", "0070_trashedrows")]
    migrate_to = [("database", "0071_alter_linkrowfield_link_row_relation_id")]

    old_state = migrate(migrate_from)

    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    table_2 = data_fixture.create_database_table(database=database)

    OldLinkRowField = old_state.apps.get_model("database", "LinkRowField")
    content_type_id = ContentType.objects.get_for_model(OldLinkRowField).id
    link_row_1 = OldLinkRowField.objects.create(
        table_id=table.id,
        link_row_table_id=table_2.id,
        link_row_relation_id=2,
        link_row_related_field_id=None,
        content_type_id=content_type_id,
        order=0,
    )
    link_row_2 = OldLinkRowField(
        table_id=table_2.id,
        link_row_table_id=table.id,
        link_row_relation_id=2,
        link_row_related_field_id=link_row_1.id,
        content_type_id=content_type_id,
        order=1,
    )
    link_row_1.link_row_related_field_id = link_row_2.id
    link_row_1.save()

    new_state = migrate(migrate_to)

    LinkRowField = new_state.apps.get_model("database", "LinkRowField")
    link_row_1 = LinkRowField.objects.get(pk=link_row_1.id)
    link_row_2 = LinkRowField.objects.get(pk=link_row_1.id)

    assert link_row_1.link_row_relation_id == 2
    assert link_row_2.link_row_relation_id == 2

    link_row_3 = data_fixture.create_link_row_field(
        table=table,
        link_row_table=table_2,
        link_row_related_field=None,
        create_field=False,
    )
    link_row_4 = data_fixture.create_link_row_field(
        table=table_2,
        link_row_table=table,
        link_row_related_field=link_row_3,
        link_row_relation_id=3,
        create_field=False,
    )

    assert link_row_3.link_row_relation_id == 3
    assert link_row_4.link_row_relation_id == 3

    link_row_5 = data_fixture.create_link_row_field(
        table=table,
        link_row_table=table_2,
        link_row_related_field=None,
        create_field=False,
    )
    assert link_row_5.link_row_relation_id == 4


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state
