from django.db.models import F

import pytest
from pytest_unordered import unordered

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.expressions import (
    BaserowTableFileUniques,
    BaserowTableRowCount,
)
from baserow.contrib.database.table.models import Table
from baserow.core.usage.registries import USAGE_UNIT_MB
from baserow.core.user_files.models import UserFile


@pytest.mark.django_db
def test_get_database_table_row_count(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    RowHandler().create_rows(user, table, [{}] * 12)

    counts = Table.objects.annotate(row_count=BaserowTableRowCount(F("id")))

    assert list(counts.values("id", "row_count")) == [{"id": table.id, "row_count": 12}]

    RowHandler().create_rows(user, table, [{}] * 23)

    assert list(counts.values("id", "row_count")) == [{"id": table.id, "row_count": 35}]


@pytest.mark.django_db
def test_get_database_table_storage_usage(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_file_field(table=table)

    file_1 = data_fixture.create_user_file(size=2 * USAGE_UNIT_MB)
    file_2 = data_fixture.create_user_file(size=3 * USAGE_UNIT_MB)
    file_3 = data_fixture.create_user_file(size=5 * USAGE_UNIT_MB)

    RowHandler().create_rows(
        user,
        table,
        [
            {
                field.db_column: [
                    {"name": file_1.name, "visible_name": "new name"},
                ]
            }
        ],
    )

    qs = UserFile.objects.filter(unique__in=BaserowTableFileUniques(table.id))
    assert qs.count() == 1
    assert list(qs.values_list("id", flat=True)) == [file_1.id]

    RowHandler().create_rows(
        user,
        table,
        [
            {
                field.db_column: [
                    {"name": file_1.name, "visible_name": "new name"},
                ]
            }
        ],
    )

    qs = UserFile.objects.filter(unique__in=BaserowTableFileUniques(table.id))
    assert qs.count() == 1
    assert list(qs.values_list("id", flat=True)) == [file_1.id]

    RowHandler().create_rows(
        user,
        table,
        [
            {
                field.db_column: [
                    {"name": file_2.name, "visible_name": "new name 2"},
                    {"name": file_3.name, "visible_name": "new name 3"},
                ]
            }
        ],
    )

    qs = UserFile.objects.filter(unique__in=BaserowTableFileUniques(table.id))
    assert qs.count() == 3
    assert list(qs.values_list("id", flat=True)) == unordered(
        [file_1.id, file_2.id, file_3.id]
    )
