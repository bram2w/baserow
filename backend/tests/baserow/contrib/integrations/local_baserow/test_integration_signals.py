import pytest

from baserow.contrib.database.fields.field_types import UUIDFieldType
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.table.handler import TableHandler


@pytest.mark.django_db()
def test_local_baserow_upsert_row_handle_field_mapping_field_changes(
    data_fixture,
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    integration = data_fixture.create_local_baserow_integration(user=user)
    table = TableHandler().create_table_and_fields(
        user=user,
        database=database,
        name=data_fixture.fake.name(),
        fields=[("My field", "number", {})],
    )
    field = table.field_set.get().specific
    service = data_fixture.create_local_baserow_upsert_row_service(
        table=table,
        integration=integration,
    )
    mapping = service.field_mappings.create(field=field, value=f"42")

    # Changing from a writable field to a read-only field deletes the mapping.
    FieldHandler().update_field(user, field, UUIDFieldType.type)
    assert service.field_mappings.filter(pk=mapping.pk).exists() is False
