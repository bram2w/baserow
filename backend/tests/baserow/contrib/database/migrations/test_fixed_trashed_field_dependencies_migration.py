import pytest
from django.core.exceptions import ObjectDoesNotExist

# noinspection PyPep8Naming
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

# noinspection PyPep8Naming


@pytest.mark.django_db
def test_forwards_migration(data_fixture, transactional_db, django_assert_num_queries):
    migrate_from = [("database", "0047_fix_date_diff")]
    migrate_to = [("database", "0048_fix_trashed_field_dependencies")]

    old_state = migrate(migrate_from)

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    other_table = data_fixture.create_database_table(user=user, database=table.database)
    data_fixture.create_text_field(
        user=user, table=other_table, name="text", primary=True
    )
    text_field = data_fixture.create_text_field(
        user=user, table=table, name="text", primary=True
    )
    FieldDependency = old_state.apps.get_model("database", "FieldDependency")
    FormulaField = old_state.apps.get_model("database", "FormulaField")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    LinkRowField = old_state.apps.get_model("database", "LinkRowField")
    formula_content_type_id = ContentType.objects.get_for_model(FormulaField).id
    link_row_content_type_id = ContentType.objects.get_for_model(LinkRowField).id
    trashed_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"'a'",
        content_type_id=formula_content_type_id,
        version=2,
        requires_refresh_after_insert=False,
        order=0,
        name="trashed",
        trashed=True,
    )
    not_trashed_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"'a'",
        content_type_id=formula_content_type_id,
        order=0,
        requires_refresh_after_insert=False,
        version=2,
        name="not trashed",
        trashed=False,
    )
    trashed_link_row_field = LinkRowField.objects.create(
        table_id=table.id,
        content_type_id=link_row_content_type_id,
        link_row_table_id=other_table.id,
        name="trashed link",
        order=1,
        trashed=True,
    )
    not_trashed_link_row_field = LinkRowField.objects.create(
        table_id=table.id,
        content_type_id=link_row_content_type_id,
        link_row_table_id=table.id,
        name="not trashed link",
        order=0,
        trashed=False,
    )
    deps_that_migration_should_delete = [
        FieldDependency.objects.create(
            dependant=trashed_field, dependency=not_trashed_field
        ),
        FieldDependency.objects.create(
            dependant=trashed_field, broken_reference_field_name="a"
        ),
        FieldDependency.objects.create(
            dependant=trashed_field,
            via=not_trashed_link_row_field,
            dependency=not_trashed_field,
        ),
        FieldDependency.objects.create(
            dependant=trashed_field,
            via=trashed_link_row_field,
            dependency=not_trashed_field,
        ),
        FieldDependency.objects.create(
            dependant=trashed_field,
            via=trashed_link_row_field,
            broken_reference_field_name="a",
        ),
        FieldDependency.objects.create(
            dependant=trashed_field,
            via=trashed_link_row_field,
            dependency=trashed_field,
        ),
        FieldDependency.objects.create(
            dependant=not_trashed_field, dependency=trashed_field
        ),
        FieldDependency.objects.create(
            dependant=not_trashed_field,
            via=trashed_link_row_field,
            dependency=not_trashed_field,
        ),
        FieldDependency.objects.create(
            dependant=not_trashed_field,
            via=not_trashed_link_row_field,
            dependency=trashed_field,
        ),
        FieldDependency.objects.create(
            dependant=not_trashed_field,
            via=trashed_link_row_field,
            broken_reference_field_name="a",
        ),
    ]
    deps_that_migration_should_ignore = [
        FieldDependency.objects.create(
            dependant=not_trashed_field, dependency=not_trashed_field
        ),
        FieldDependency.objects.create(
            dependant=not_trashed_field, dependency_id=text_field.id
        ),
        FieldDependency.objects.create(
            dependant=not_trashed_field, broken_reference_field_name="a"
        ),
        FieldDependency.objects.create(
            dependant=not_trashed_field,
            via=not_trashed_link_row_field,
            dependency=not_trashed_field,
        ),
        FieldDependency.objects.create(
            dependant=not_trashed_field,
            via=not_trashed_link_row_field,
            dependency_id=text_field.id,
        ),
        FieldDependency.objects.create(
            dependant=not_trashed_field,
            via=not_trashed_link_row_field,
            broken_reference_field_name="a",
        ),
    ]
    with django_assert_num_queries(12):
        new_state = migrate(migrate_to)
    NewFieldDependency = new_state.apps.get_model("database", "FieldDependency")
    assert NewFieldDependency.objects.count() == len(deps_that_migration_should_ignore)

    def same_id_or_both_none(a, b):
        if a is None:
            assert b is None
        else:
            assert b is not None
            assert a.id == b.id

    for dep in deps_that_migration_should_ignore:
        new_dep = NewFieldDependency.objects.get(id=dep.id)
        same_id_or_both_none(new_dep.dependency, dep.dependency)
        same_id_or_both_none(new_dep.dependant, dep.dependant)
        same_id_or_both_none(new_dep.via, dep.via)
        assert new_dep.broken_reference_field_name == dep.broken_reference_field_name

    for dep in deps_that_migration_should_delete:
        with pytest.raises(ObjectDoesNotExist):
            NewFieldDependency.objects.get(id=dep.id)


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state
