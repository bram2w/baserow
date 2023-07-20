from datetime import datetime

from django.utils import timezone

import pytest
import pytz
from freezegun import freeze_time

from baserow.contrib.database.fields.field_types import FormulaFieldType
from baserow.contrib.database.fields.tasks import run_periodic_fields_updates
from baserow.core.trash.handler import TrashHandler


@pytest.mark.django_db
def test_run_periodic_field_type_update_per_non_existing_workspace_does_nothing(
    django_assert_num_queries,
):
    with django_assert_num_queries(1):
        run_periodic_fields_updates(workspace_id=9999)


@pytest.mark.django_db
def test_run_periodic_fields_updates(data_fixture):
    user = data_fixture.create_user()

    def create_table_with_row_in_workspace(workspace):
        database = data_fixture.create_database_application(workspace=workspace)
        table = data_fixture.create_database_table(database=database)
        formula_field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )
        return table.get_model(), formula_field

    # when the workspace is created the now field is set to the current time
    with freeze_time("2023-02-27 9:55"):
        workspace = data_fixture.create_workspace(user=user)
        table_model, formula_field = create_table_with_row_in_workspace(workspace)
        row = table_model.objects.create()

        workspace_2 = data_fixture.create_workspace(user=user)
        table_model_2, formula_field_2 = create_table_with_row_in_workspace(workspace_2)
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

    workspace.refresh_from_db()
    workspace_2.refresh_from_db()

    assert workspace.now == datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)
    assert workspace_2.now == datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)

    # the task can be run without updating the now field
    with freeze_time("2023-02-27 10:15"):
        run_periodic_fields_updates(update_now=False)

    workspace.refresh_from_db()
    workspace_2.refresh_from_db()

    assert workspace.now == datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)
    assert workspace_2.now == datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)


@pytest.mark.django_db
def test_run_periodic_field_type_update_per_workspace(data_fixture):
    workspace = data_fixture.create_workspace()

    database = data_fixture.create_database_application(workspace=workspace)
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
        run_periodic_fields_updates(workspace_id=workspace.id)

        row.refresh_from_db()
        assert getattr(row, f"field_{field.id}") == datetime(
            2023, 2, 27, 10, 30, 0, tzinfo=pytz.UTC
        )


@pytest.mark.django_db
def test_run_field_type_updates_dependant_fields(data_fixture):
    workspace = data_fixture.create_workspace()

    database = data_fixture.create_database_application(workspace=workspace)
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
        run_periodic_fields_updates(workspace_id=workspace.id)

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
def test_workspace_updated_last_will_be_updated_first_this_time(data_fixture):
    user = data_fixture.create_user()

    def create_table_with_now_in_workspace(workspace):
        database = data_fixture.create_database_application(workspace=workspace)
        table = data_fixture.create_database_table(database=database)
        formula_field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )
        return table.get_model(), formula_field

    # when the workspace is created the now field is set to the current time
    now = timezone.now()
    workspace_updated_most_recently = data_fixture.create_workspace(user=user)
    workspace_updated_most_recently.now = now
    workspace_updated_most_recently.save()
    table_model, formula_field = create_table_with_now_in_workspace(
        workspace_updated_most_recently
    )
    row = table_model.objects.create()

    a_day_ago = timezone.now() - timezone.timedelta(days=1)
    workspace_that_should_be_updated_first_this_time = data_fixture.create_workspace(
        user=user
    )
    workspace_that_should_be_updated_first_this_time.now = a_day_ago
    workspace_that_should_be_updated_first_this_time.save()
    table_model_2, formula_field_2 = create_table_with_now_in_workspace(
        workspace_that_should_be_updated_first_this_time
    )
    row_2 = table_model_2.objects.create()

    assert a_day_ago < now
    assert a_day_ago == workspace_that_should_be_updated_first_this_time.now
    assert (
        workspace_that_should_be_updated_first_this_time.now
        < workspace_updated_most_recently.now
    )

    run_periodic_fields_updates()

    workspace_updated_most_recently.refresh_from_db()
    workspace_that_should_be_updated_first_this_time.refresh_from_db()

    assert workspace_that_should_be_updated_first_this_time.now != a_day_ago
    assert workspace_updated_most_recently.now != now
    # The first workspace that got updated will have the lowest now value
    assert (
        workspace_that_should_be_updated_first_this_time.now
        < workspace_updated_most_recently.now
    )


@pytest.mark.django_db
def test_one_formula_failing_doesnt_block_others(data_fixture):
    user = data_fixture.create_user()

    def create_table_with_now_in_workspace(workspace):
        database = data_fixture.create_database_application(workspace=workspace)
        table = data_fixture.create_database_table(database=database)
        formula_field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )
        return table.get_model(), formula_field

    # when the workspace is created the now field is set to the current time
    now = timezone.now()
    second_updated_workspace = data_fixture.create_workspace(user=user)
    second_updated_workspace.now = now
    second_updated_workspace.save()
    table_model, working_other_formula = create_table_with_now_in_workspace(
        second_updated_workspace
    )
    row = table_model.objects.create()

    a_day_ago = timezone.now() - timezone.timedelta(days=1)
    first_updated_workspace = data_fixture.create_workspace(user=user)
    first_updated_workspace.now = a_day_ago
    first_updated_workspace.save()
    table_model_2, broken_first_formula = create_table_with_now_in_workspace(
        first_updated_workspace
    )
    row_2 = table_model_2.objects.create()
    broken_first_formula.internal_formula = "broken"
    broken_first_formula.save(recalculate=False)

    assert a_day_ago < now
    assert a_day_ago == first_updated_workspace.now
    assert first_updated_workspace.now < second_updated_workspace.now

    assert getattr(row, f"field_{working_other_formula.id}") == now
    assert getattr(row_2, f"field_{broken_first_formula.id}") == a_day_ago

    run_periodic_fields_updates()

    row_2.refresh_from_db()
    # It didn't get refreshed
    assert getattr(row_2, f"field_{broken_first_formula.id}") == a_day_ago
    row.refresh_from_db()
    # It did get refreshed
    assert getattr(row, f"field_{working_other_formula.id}") != now

    second_updated_workspace.refresh_from_db()
    first_updated_workspace.refresh_from_db()

    assert first_updated_workspace.now != a_day_ago
    assert second_updated_workspace.now != now
    assert first_updated_workspace.now < second_updated_workspace.now


@pytest.mark.django_db
def test_all_formula_that_needs_updates_are_periodically_updated(data_fixture):
    workspace = data_fixture.create_workspace()

    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    with freeze_time("2023-02-27 10:15"):
        now_field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )
        data_fixture.create_formula_field(
            table=table,
            formula=f"field('{now_field.name}')",
            date_include_time=True,
        )

        date_field = data_fixture.create_date_field(table=table, date_include_time=True)
        data_fixture.create_formula_field(
            table=table,
            formula=f"now() > field('{date_field.name}')",
            date_include_time=True,
        )

        assert FormulaFieldType().get_fields_needing_periodic_update().count() == 3


@pytest.mark.django_db
def test_run_periodic_field_type_doesnt_update_trashed_table(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)

    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)

    original_datetime = datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)

    with freeze_time(original_datetime):
        field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )

    table_model = table.get_model()
    row = table_model.objects.create()

    assert getattr(row, f"field_{field.id}") == original_datetime

    TrashHandler.trash(user, workspace, database, table)

    with freeze_time("2023-02-27 10:30"):
        run_periodic_fields_updates(workspace_id=workspace.id)

        row.refresh_from_db()
        assert getattr(row, f"field_{field.id}") == original_datetime

        assert FormulaFieldType().get_fields_needing_periodic_update().count() == 0


@pytest.mark.django_db
def test_run_periodic_field_type_doesnt_update_trashed_database(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)

    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)

    original_datetime = datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)

    with freeze_time(original_datetime):
        field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )

    table_model = table.get_model()
    row = table_model.objects.create()

    assert getattr(row, f"field_{field.id}") == original_datetime

    TrashHandler.trash(user, workspace, database, database)

    with freeze_time("2023-02-27 10:30"):
        run_periodic_fields_updates(workspace_id=workspace.id)

        row.refresh_from_db()
        assert getattr(row, f"field_{field.id}") == original_datetime

        assert FormulaFieldType().get_fields_needing_periodic_update().count() == 0


@pytest.mark.django_db
def test_run_periodic_field_type_doesnt_update_trashed_workspace(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)

    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)

    original_datetime = datetime(2023, 2, 27, 10, 0, 0, tzinfo=pytz.UTC)

    with freeze_time(original_datetime):
        field = data_fixture.create_formula_field(
            table=table, formula="now()", date_include_time=True
        )

    table_model = table.get_model()
    row = table_model.objects.create()

    assert getattr(row, f"field_{field.id}") == original_datetime

    TrashHandler.trash(user, workspace, None, workspace)

    with freeze_time("2023-02-27 10:30"):
        run_periodic_fields_updates(workspace_id=workspace.id)

        row.refresh_from_db()
        assert getattr(row, f"field_{field.id}") == original_datetime

        assert FormulaFieldType().get_fields_needing_periodic_update().count() == 0
