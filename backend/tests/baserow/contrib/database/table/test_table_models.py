import pytest

from baserow.contrib.database.table.models import Table


@pytest.mark.django_db
def test_group_user_get_next_order(data_fixture):
    database = data_fixture.create_database_application()
    database_2 = data_fixture.create_database_application()
    data_fixture.create_database_table(order=1, database=database)
    data_fixture.create_database_table(order=2, database=database)
    data_fixture.create_database_table(order=10, database=database_2)

    assert Table.get_last_order(database) == 3
    assert Table.get_last_order(database_2) == 11
