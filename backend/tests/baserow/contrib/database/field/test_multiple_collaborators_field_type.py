from io import BytesIO

from django.apps.registry import apps

import pytest
from faker import Faker

from baserow.contrib.database.fields.field_types import MultipleCollaboratorsFieldType
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import MultipleCollaboratorsField
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.handler import ViewHandler
from baserow.core.handler import CoreHandler


@pytest.mark.django_db
@pytest.mark.field_multiple_collaborators
def test_multiple_collaborators_field_type_create(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    collaborator_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_collaborators",
        name="Collaborator 1",
    )
    field_id = collaborator_field.db_column

    assert MultipleCollaboratorsField.objects.all().first().id == collaborator_field.id

    row = row_handler.create_row(
        user=user, table=table, values={field_id: [{"id": user.id}]}
    )
    assert row.id
    collaborator_field_list = getattr(row, field_id).all()
    assert len(collaborator_field_list) == 1
    assert collaborator_field_list[0].id == user.id


@pytest.mark.django_db
@pytest.mark.field_multiple_collaborators
def test_multiple_collaborators_field_type_update(data_fixture):
    group = data_fixture.create_group()
    user = data_fixture.create_user(group=group)
    user2 = data_fixture.create_user(group=group)
    user3 = data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(
        user=user, name="Placeholder", group=group
    )
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    collaborator_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_collaborators",
        name="Collaborator 1",
    )
    field_id = collaborator_field.db_column

    assert MultipleCollaboratorsField.objects.all().first().id == collaborator_field.id

    row = row_handler.create_row(user=user, table=table, values={field_id: []})

    row_handler.update_row(
        user, table, row, {field_id: [{"id": user2.id}, {"id": user3.id}]}
    )

    collaborator_field_list = getattr(row, field_id).all().order_by("id")
    assert len(collaborator_field_list) == 2
    assert collaborator_field_list[0].id == user2.id
    assert collaborator_field_list[1].id == user3.id


@pytest.mark.django_db(transaction=True)
def test_get_set_export_serialized_value_multiple_collaborators_field(data_fixture):
    user = data_fixture.create_user(email="user1@baserow.io")
    user_2 = data_fixture.create_user(email="user2@baserow.io")
    user_3 = data_fixture.create_user(email="user3@baserow.io")
    group = data_fixture.create_group(user=user)
    data_fixture.create_user_group(group=group, user=user_2)
    data_fixture.create_user_group(group=group, user=user_3)

    imported_group = data_fixture.create_group(user=user)
    data_fixture.create_user_group(group=imported_group, user=user_2)
    database = data_fixture.create_database_application(group=group)
    table = data_fixture.create_database_table(database=database)
    field_handler = FieldHandler()
    row_handler = RowHandler()
    core_handler = CoreHandler()

    multiple_collaborators__field = field_handler.create_field(
        user=user,
        table=table,
        name="Multiple collaborators",
        type_name="multiple_collaborators",
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={},
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{multiple_collaborators__field.id}": [
                {"id": user.id},
                {"id": user_2.id},
            ],
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        values={
            f"field_{multiple_collaborators__field.id}": [
                {"id": user.id},
                {"id": user_3.id},
            ],
        },
    )

    exported_applications = core_handler.export_group_applications(group, BytesIO())
    imported_applications, id_mapping = core_handler.import_applications_to_group(
        imported_group, exported_applications, BytesIO(), None
    )
    imported_database = imported_applications[0]
    imported_table = imported_database.table_set.all()[0]
    imported_field = imported_table.field_set.all().first().specific

    assert imported_table.id != table.id
    assert imported_field.id != multiple_collaborators__field.id

    imported_model = imported_table.get_model()
    all = imported_model.objects.all()
    assert len(all) == 3
    imported_row_1 = all[0]
    imported_row_1_field = (
        getattr(imported_row_1, f"field_" f"{imported_field.id}").order_by("id").all()
    )
    imported_row_2 = all[1]
    imported_row_2_field = (
        getattr(imported_row_2, f"field_{imported_field.id}").order_by("id").all()
    )
    imported_row_3 = all[2]
    imported_row_3_field = (
        getattr(imported_row_3, f"field_{imported_field.id}").order_by("id").all()
    )

    assert len(imported_row_1_field) == 0
    assert len(imported_row_2_field) == 2
    assert imported_row_2_field[0].id == user.id
    assert imported_row_2_field[1].id == user_2.id
    assert len(imported_row_3_field) == 1
    assert imported_row_3_field[0].id == user.id


@pytest.mark.django_db
def test_multiple_collaborators_field_type_sorting(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user(email="user1@baserow.io", first_name="User 1")
    user_2 = data_fixture.create_user(email="user2@baserow.io", first_name="User 2")
    user_3 = data_fixture.create_user(email="user3@baserow.io", first_name="User 3")
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    data_fixture.create_user_group(group=database.group, user=user_2)
    data_fixture.create_user_group(group=database.group, user=user_3)
    table = data_fixture.create_database_table(name="Example", database=database)
    grid_view = data_fixture.create_grid_view(table=table)

    field_handler = FieldHandler()
    view_handler = ViewHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        name="Multiple Collaborators",
        type_name="multiple_collaborators",
    )

    row_1 = data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user.id}, {"id": user_2.id}, {"id": user_3.id}],
        user=user,
    )
    row_2 = data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user_3.id}, {"id": user_2.id}, {"id": user.id}],
        user=user,
    )
    row_3 = data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, values=[{"id": user_3.id}, {"id": user.id}], user=user
    )
    row_4 = data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, values=[{"id": user_2.id}], user=user
    )
    row_5 = data_fixture.create_row_for_many_to_many_field(
        table=table, field=field, values=[], user=user
    )

    sort = data_fixture.create_view_sort(view=grid_view, field=field, order="ASC")
    model = table.get_model()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_5.id, row_1.id, row_4.id, row_3.id, row_2.id]

    sort.order = "DESC"
    sort.save()

    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_2.id, row_3.id, row_4.id, row_1.id, row_5.id]


@pytest.mark.django_db
def test_call_apps_registry_pending_operations(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()
    field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_collaborators",
        name="Test",
    )
    table.get_model()
    # Make sure that there are no pending operations in the app registry. Because a
    # Django ManyToManyField registers pending operations every time a table model is
    # generated, which can causes a memory leak if they are not triggered.
    assert len(apps._pending_operations) == 0


@pytest.mark.django_db
def test_multiple_collaborators_model_field(data_fixture):
    user = data_fixture.create_user(email="user1@baserow.io", first_name="User 1")
    user_2 = data_fixture.create_user(email="user2@baserow.io", first_name="User 2")
    user_3 = data_fixture.create_user(email="user3@baserow.io", first_name="User 3")
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    data_fixture.create_user_group(group=database.group, user=user_2)
    group_user_3 = data_fixture.create_user_group(group=database.group, user=user_3)
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()
    field = field_handler.create_field(
        user=user,
        table=table,
        name="Multiple Collaborators",
        type_name="multiple_collaborators",
    )

    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user.id}, {"id": user_2.id}],
        user=user,
    )
    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user_2.id}, {"id": user_3.id}],
        user=user,
    )
    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user_3.id}, {"id": user_2.id}, {"id": user.id}],
        user=user,
    )

    model = table.get_model()
    rows = list(model.objects.all().order_by("id"))

    row_1_relations = getattr(rows[0], f"field_{field.id}").all()
    row_1_relation_ids = [u.id for u in row_1_relations]
    assert row_1_relation_ids == [user.id, user_2.id]

    row_2_relations = getattr(rows[1], f"field_{field.id}").all()
    row_2_relation_ids = [u.id for u in row_2_relations]
    assert row_2_relation_ids == [user_2.id, user_3.id]

    row_3_relations = getattr(rows[2], f"field_{field.id}").all()
    row_3_relation_ids = [u.id for u in row_3_relations]
    assert row_3_relation_ids == [user_3.id, user_2.id, user.id]

    # After deleting group user 3, we don't expect user_3 to be returned here anymore.
    group_user_3.delete()

    rows = list(model.objects.all().order_by("id"))

    row_1_relations = getattr(rows[0], f"field_{field.id}").all()
    row_1_relation_ids = [u.id for u in row_1_relations]
    assert row_1_relation_ids == [user.id, user_2.id]

    row_2_relations = getattr(rows[1], f"field_{field.id}").all()
    row_2_relation_ids = [u.id for u in row_2_relations]
    assert row_2_relation_ids == [user_2.id]

    row_3_relations = getattr(rows[2], f"field_{field.id}").all()
    row_3_relation_ids = [u.id for u in row_3_relations]
    assert row_3_relation_ids == [user_2.id, user.id]


@pytest.mark.django_db
def test_multiple_collaborators_model_enhanced_field(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user(email="user1@baserow.io", first_name="User 1")
    user_2 = data_fixture.create_user(email="user2@baserow.io", first_name="User 2")
    user_3 = data_fixture.create_user(email="user3@baserow.io", first_name="User 3")
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    data_fixture.create_user_group(group=database.group, user=user_2)
    group_user_3 = data_fixture.create_user_group(group=database.group, user=user_3)
    table = data_fixture.create_database_table(name="Example", database=database)

    field_handler = FieldHandler()
    field = field_handler.create_field(
        user=user,
        table=table,
        name="Multiple Collaborators",
        type_name="multiple_collaborators",
    )

    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user.id}, {"id": user_2.id}],
        user=user,
    )
    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user_2.id}, {"id": user_3.id}],
        user=user,
    )
    data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user_3.id}, {"id": user_2.id}, {"id": user.id}],
        user=user,
    )

    model = table.get_model()

    with django_assert_num_queries(2):
        rows = list(model.objects.all().order_by("id").enhance_by_fields())

        row_1_relations = getattr(rows[0], f"field_{field.id}").all()
        row_1_relation_ids = [u.id for u in row_1_relations]
        assert row_1_relation_ids == [user.id, user_2.id]

        row_2_relations = getattr(rows[1], f"field_{field.id}").all()
        row_2_relation_ids = [u.id for u in row_2_relations]
        assert row_2_relation_ids == [user_2.id, user_3.id]

        row_3_relations = getattr(rows[2], f"field_{field.id}").all()
        row_3_relation_ids = [u.id for u in row_3_relations]
        assert row_3_relation_ids == [user_3.id, user_2.id, user.id]

    # After deleting group user 3, we don't expect user_3 to be returned here anymore.
    group_user_3.delete()

    with django_assert_num_queries(2):
        rows = list(model.objects.all().order_by("id").enhance_by_fields())

        row_1_relations = getattr(rows[0], f"field_{field.id}").all()
        row_1_relation_ids = [u.id for u in row_1_relations]
        assert row_1_relation_ids == [user.id, user_2.id]

        row_2_relations = getattr(rows[1], f"field_{field.id}").all()
        row_2_relation_ids = [u.id for u in row_2_relations]
        assert row_2_relation_ids == [user_2.id]

        row_3_relations = getattr(rows[2], f"field_{field.id}").all()
        row_3_relation_ids = [u.id for u in row_3_relations]
        assert row_3_relation_ids == [user_2.id, user.id]


@pytest.mark.django_db
def test_multiple_collaborators_field_type_random_value(data_fixture):
    group = data_fixture.create_group()
    user = data_fixture.create_user(group=group)
    user2 = data_fixture.create_user(group=group)
    user3 = data_fixture.create_user(group=group)
    database = data_fixture.create_database_application(
        user=user, group=group, name="database"
    )
    table = data_fixture.create_database_table(name="table", database=database)
    field_handler = FieldHandler()
    cache = {}
    fake = Faker()

    field = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_collaborators",
        name="Multiple collaborators",
    )

    possible_collaborators = [user, user2, user3]
    random_choice = MultipleCollaboratorsFieldType().random_value(field, fake, cache)
    assert type(random_choice) is list
    assert (
        set([x.id for x in possible_collaborators]).issuperset(set(random_choice))
        is True
    )

    random_choice = MultipleCollaboratorsFieldType().random_value(field, fake, cache)
    assert type(random_choice) is list
    assert (
        set([x.id for x in possible_collaborators]).issuperset(set(random_choice))
        is True
    )


@pytest.mark.django_db
def test_multiple_collaborators_field_adjacent_row(data_fixture):
    group = data_fixture.create_group()
    user = data_fixture.create_user(group=group, first_name="User 1")
    user_2 = data_fixture.create_user(group=group, first_name="User 2")
    user_3 = data_fixture.create_user(group=group, first_name="User 3")
    database = data_fixture.create_database_application(
        user=user, group=group, name="database"
    )
    table = data_fixture.create_database_table(name="table", database=database)
    grid_view = data_fixture.create_grid_view(table=table)
    field_handler = FieldHandler()

    field = field_handler.create_field(
        user=user,
        table=table,
        type_name="multiple_collaborators",
        name="Multiple collaborators",
    )

    data_fixture.create_view_sort(view=grid_view, field=field, order="DESC")

    row_a = data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user.id}],
        user=user,
    )
    row_b = data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user_2.id}],
        user=user,
    )
    row_c = data_fixture.create_row_for_many_to_many_field(
        table=table,
        field=field,
        values=[{"id": user_3.id}],
        user=user,
    )

    base_queryset = table.get_model().objects.all()

    row_b = base_queryset.get(pk=row_b.id)
    previous_row = RowHandler().get_adjacent_row(
        row_b, base_queryset, previous=True, view=grid_view
    )
    next_row = RowHandler().get_adjacent_row(row_b, base_queryset, view=grid_view)

    assert previous_row.id == row_c.id
    assert next_row.id == row_a.id
