from datetime import datetime

from django.utils import timezone

import pytest
import pytz
from freezegun import freeze_time

from baserow.contrib.database.fields.tasks import run_periodic_fields_updates


@pytest.mark.django_db
def test_run_periodic_field_type_update_per_non_existing_group_does_nothing(
    django_assert_num_queries,
):
    with django_assert_num_queries(1):
        run_periodic_fields_updates(group_id=9999)


@pytest.mark.django_db
def test_run_periodic_fields_updates(data_fixture):
    user = data_fixture.create_user()

    def create_table_with_row_in_group(group):
        database = data_fixture.create_database_application(group=group)
        table = data_fixture.create_database_table(database=database)
        formula_field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )
        return table.get_model(), formula_field

    # when the group is created the now field is set to the current time
    with freeze_time("2023-02-27 9:55"):
        group = data_fixture.create_group(user=user)
        table_model, formula_field = create_table_with_row_in_group(group)
        row = table_model.objects.create()

        group_2 = data_fixture.create_group(user=user)
        table_model_2, formula_field_2 = create_table_with_row_in_group(group_2)
        row_2 = table_model_2.objects.create()

    assert getattr(row, f"field_{formula_field.id}") == datetime(
        2023, 2, 27, 9, 55, 0, tzinfo=pytz.UTC
    )
    assert getattr(row_2, f"field_{formula_field_2.id}") == datetime(
        2023, 2, 27, 9, 55, 0, tzinfo=pytz.UTC
    )

    # the now field is updated to the current time by default
    # and all the values updated accordingly
    with freeze_time("2023-02-27 10:00"):
        run_periodic_fields_updates()

    group.refresh_from_db()
    group_2.refresh_from_db()

    assert group.now == datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)
    assert group_2.now == datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)

    # the task can be run without updating the now field
    with freeze_time("2023-02-27 10:15"):
        run_periodic_fields_updates(update_now=False)

    group.refresh_from_db()
    group_2.refresh_from_db()

    assert group.now == datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)
    assert group_2.now == datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)


@pytest.mark.django_db
def test_run_periodic_field_type_update_per_group(data_fixture):
    group = data_fixture.create_group()

    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    with freeze_time("2023-02-27 10:00"):
        field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )

    table_model = table.get_model()
    row = table_model.objects.create()

    assert getattr(row, f"field_{field.id}") == datetime(
        2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC
    )

    with freeze_time("2023-02-27 10:30"):
        run_periodic_fields_updates(group_id=group.id)

        row.refresh_from_db()
        assert getattr(row, f"field_{field.id}") == datetime(
            2023, 2, 27, 10, 30, 0, tzinfo=pytz.UTC
        )


@pytest.mark.django_db
def test_run_field_type_updates_dependant_fields(data_fixture):
    group = data_fixture.create_group()

    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    with freeze_time("2023-02-27 10:15"):
        field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )
        dependant = data_fixture.create_formula_field(
            table=table, formula=f"field('{field.name}')", date_include_time=True
        )
        dependant_2 = data_fixture.create_formula_field(
            table=table, formula=f"field('{field.name}')", date_include_time=True
        )

    table_model = table.get_model()
    row = table_model.objects.create()

    assert getattr(row, f"field_{field.id}") == datetime(
        2023, 2, 27, 10, 15, 0, tzinfo=pytz.UTC
    )
    assert getattr(row, f"field_{dependant.id}") == datetime(
        2023, 2, 27, 10, 15, 0, tzinfo=pytz.UTC
    )
    assert getattr(row, f"field_{dependant_2.id}") == datetime(
        2023, 2, 27, 10, 15, 0, tzinfo=pytz.UTC
    )

    with freeze_time("2023-02-27 10:45"):
        run_periodic_fields_updates(group_id=group.id)

        row.refresh_from_db()
        assert getattr(row, f"field_{field.id}") == datetime(
            2023, 2, 27, 10, 45, 0, tzinfo=pytz.UTC
        )
        assert getattr(row, f"field_{dependant.id}") == datetime(
            2023, 2, 27, 10, 45, 0, tzinfo=pytz.UTC
        )
        assert getattr(row, f"field_{dependant_2.id}") == datetime(
            2023, 2, 27, 10, 45, 0, tzinfo=pytz.UTC
        )


@pytest.mark.django_db
def test_group_updated_last_will_be_updated_first_this_time(data_fixture):
    user = data_fixture.create_user()

    def create_table_with_row_in_group(group):
        database = data_fixture.create_database_application(group=group)
        table = data_fixture.create_database_table(database=database)
        formula_field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )
        return table.get_model(), formula_field

    # when the group is created the now field is set to the current time
    now = timezone.now()
    group_updated_most_recently = data_fixture.create_group(user=user)
    group_updated_most_recently.now = now
    group_updated_most_recently.save()
    table_model, formula_field = create_table_with_row_in_group(
        group_updated_most_recently
    )
    row = table_model.objects.create()

    a_day_ago = timezone.now() - timezone.timedelta(days=1)
    group_that_should_be_updated_first_this_time = data_fixture.create_group(user=user)
    group_that_should_be_updated_first_this_time.now = a_day_ago
    group_that_should_be_updated_first_this_time.save()
    table_model_2, formula_field_2 = create_table_with_row_in_group(
        group_that_should_be_updated_first_this_time
    )
    row_2 = table_model_2.objects.create()

    assert a_day_ago < now
    assert a_day_ago == group_that_should_be_updated_first_this_time.now
    assert (
        group_that_should_be_updated_first_this_time.now
        < group_updated_most_recently.now
    )

    run_periodic_fields_updates()

    group_updated_most_recently.refresh_from_db()
    group_that_should_be_updated_first_this_time.refresh_from_db()

    assert group_that_should_be_updated_first_this_time.now != a_day_ago
    assert group_updated_most_recently.now != now
    # The first group that got updated will have the lowest now value
    assert (
        group_that_should_be_updated_first_this_time.now
        < group_updated_most_recently.now
    )


@pytest.mark.django_db
def test_one_formula_failing_doesnt_block_others(data_fixture):
    user = data_fixture.create_user()

    def create_table_with_row_in_group(group):
        database = data_fixture.create_database_application(group=group)
        table = data_fixture.create_database_table(database=database)
        formula_field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )
        return table.get_model(), formula_field

    # when the group is created the now field is set to the current time
    now = timezone.now()
    second_updated_group = data_fixture.create_group(user=user)
    second_updated_group.now = now
    second_updated_group.save()
    table_model, working_other_formula = create_table_with_row_in_group(
        second_updated_group
    )
    row = table_model.objects.create()

    a_day_ago = timezone.now() - timezone.timedelta(days=1)
    first_updated_group = data_fixture.create_group(user=user)
    first_updated_group.now = a_day_ago
    first_updated_group.save()
    table_model_2, broken_first_formula = create_table_with_row_in_group(
        first_updated_group
    )
    row_2 = table_model_2.objects.create()
    broken_first_formula.internal_formula = "broken"
    broken_first_formula.save(recalculate=False)

    assert a_day_ago < now
    assert a_day_ago == first_updated_group.now
    assert first_updated_group.now < second_updated_group.now

    assert getattr(row, f"field_{working_other_formula.id}") == now
    assert getattr(row_2, f"field_{broken_first_formula.id}") == a_day_ago

    run_periodic_fields_updates()

    row_2.refresh_from_db()
    # It didn't get refreshed
    assert getattr(row_2, f"field_{broken_first_formula.id}") == a_day_ago
    row.refresh_from_db()
    # It did get refreshed
    assert getattr(row, f"field_{working_other_formula.id}") != now

    second_updated_group.refresh_from_db()
    first_updated_group.refresh_from_db()

    assert first_updated_group.now != a_day_ago
    assert second_updated_group.now != now
    assert first_updated_group.now < second_updated_group.now
