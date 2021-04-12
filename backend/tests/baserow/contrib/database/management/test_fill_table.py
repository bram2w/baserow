import pytest
from io import StringIO

from django.core.management import call_command


@pytest.mark.django_db
def test_fill_table_no_table():
    """
    Check whether calling the fille_table command correctly 'raises' a system exit
    when the command gets called with a table that does not exist
    """

    output = StringIO()
    table_id_that_does_not_exist = 5

    with pytest.raises(SystemExit) as sys_exit:
        call_command("fill_table", table_id_that_does_not_exist, 10, stdout=output)
    assert sys_exit.type == SystemExit
    assert sys_exit.value.code == 1

    assert (
        output.getvalue()
        == f"The table with id {table_id_that_does_not_exist} was not found.\n"
    )


@pytest.mark.django_db
@pytest.mark.parametrize("test_limit", [5, 10])
def test_fill_table_empty_table(data_fixture, test_limit):
    """
    Verify that the fill_table command correctly populates a given empty table with
    different 'limit' rows
    """

    # create a new empty table with a text field
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(user=user, table=table)

    call_command("fill_table", table.id, test_limit)

    model = table.get_model()
    results = model.objects.all()

    assert len(results) == test_limit


@pytest.mark.django_db
@pytest.mark.parametrize("test_limit", [5, 10])
def test_fill_table_no_empty_table(data_fixture, test_limit):
    """
    Verify that the fill_table command correctly appends to a table with data already
    in it with different 'limit' rows
    """

    # create a new empty table with a field
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(user=user, table=table)

    model = table.get_model()

    # create data in the previously created field
    values = {f"field_{text_field.id}": "Some Text"}
    model.objects.create(**values)

    results = model.objects.all()
    row_length_before_random_insert = len(results)
    first_row_value_before = getattr(results[0], f"field_{text_field.id}")

    # execute the fill_table command
    call_command("fill_table", table.id, test_limit)

    results = model.objects.all()
    first_row_value_after = getattr(results[0], f"field_{text_field.id}")

    # make sure the first row is still the same
    assert first_row_value_before == first_row_value_after
    assert len(results) == test_limit + row_length_before_random_insert
