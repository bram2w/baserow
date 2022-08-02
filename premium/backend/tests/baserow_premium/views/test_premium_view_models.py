import pytest
from baserow_premium.views.models import KanbanViewFieldOptions


@pytest.mark.django_db
def test_kanban_view_field_options_manager_view_trashed(premium_data_fixture):
    kanban_view = premium_data_fixture.create_kanban_view()

    # create_kanban_view already creates a view field option
    # which we don't want to test here
    KanbanViewFieldOptions.objects.all().delete()

    field = premium_data_fixture.create_text_field(table=kanban_view.table)
    premium_data_fixture.create_kanban_view_field_option(kanban_view, field)

    assert KanbanViewFieldOptions.objects.count() == 1

    kanban_view.trashed = True
    kanban_view.save()

    assert KanbanViewFieldOptions.objects.count() == 0


@pytest.mark.django_db
def test_kanban_view_field_options_manager_field_trashed(premium_data_fixture):
    kanban_view = premium_data_fixture.create_kanban_view()

    # create_kanban_view already creates a view field option
    # which we don't want to test here
    KanbanViewFieldOptions.objects.all().delete()

    field = premium_data_fixture.create_text_field(table=kanban_view.table)
    premium_data_fixture.create_kanban_view_field_option(kanban_view, field)

    assert KanbanViewFieldOptions.objects.count() == 1

    field.trashed = True
    field.save()

    assert KanbanViewFieldOptions.objects.count() == 0
