from django.core.management import call_command

import pytest

from baserow.contrib.database.table.models import Table


@pytest.mark.django_db
def test_debug_table_shows_table_and_field_names(data_fixture, capsys):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(user=user, table=table)

    num_columns_before = table.field_set.count()

    call_command("debug_table", table.id)

    captured = capsys.readouterr()
    assert table.name in captured.out
    assert text_field.name in captured.out

    table.refresh_from_db()
    assert table.field_set.count() == num_columns_before


@pytest.mark.django_db
def test_debug_table_raises_when_table_doesnt_exist(data_fixture):
    with pytest.raises(Table.DoesNotExist):
        call_command("debug_table", 99999)
