from unittest.mock import patch

from django.test import override_settings

import pytest
from rest_framework.exceptions import ValidationError

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.search.handler import SearchHandler
from baserow.core.embeddings import EmbeddingsServiceError
from baserow.core.pgvector import is_pgvector_enabled
from baserow.core.registries import ImportExportConfig
from baserow.core.services.exceptions import (
    ServiceImproperlyConfiguredDispatchException,
    UnexpectedDispatchException,
)
from baserow.core.services.handler import ServiceHandler
from baserow.core.services.registries import service_type_registry
from baserow.test_utils.pytest_conftest import FakeDispatchContext


@pytest.fixture
def setup(data_fixture):
    if not is_pgvector_enabled():
        pytest.skip("pgvector is not installed in the test database")
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    name = data_fixture.create_text_field(table=table, name="Name")
    with override_settings(BASEROW_EMBEDDINGS_API_URL="http://embeddings.test"):
        notes = FieldHandler().create_field(
            user, table, "long_text", name="Notes", vector_search_enabled=True
        )
    rows = (
        RowHandler()
        .create_rows(
            user,
            table,
            rows_values=[
                {f"field_{name.id}": "Apple", f"field_{notes.id}": "A fruit"},
                {f"field_{name.id}": "Truck", f"field_{notes.id}": "A vehicle"},
            ],
        )
        .created_rows
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    service_type = service_type_registry.get("local_baserow_vector_search")
    return user, table, name, notes, rows, integration, service_type


@pytest.mark.django_db
def test_vector_search_service_validates_its_fields(setup, data_fixture):
    user, table, name, notes, rows, integration, service_type = setup
    other_table = data_fixture.create_database_table(user=user)
    other_field = data_fixture.create_long_text_field(table=other_table)

    base = {"table_id": table.id, "integration_id": integration.id}
    with pytest.raises(ValidationError):
        service_type.prepare_values(
            {**base, "search_field_ids": [other_field.id]}, user
        )
    with pytest.raises(ValidationError):
        # Vector search is off on the name field.
        service_type.prepare_values(
            {**base, "search_field_ids": [notes.id, name.id]}, user
        )
    with pytest.raises(ValidationError):
        service_type.prepare_values(
            {
                **base,
                "search_field_ids": [notes.id],
                "included_field_ids": [other_field.id],
            },
            user,
        )

    values = service_type.prepare_values(
        {
            **base,
            "search_field_ids": [notes.id],
            "included_field_ids": [name.id],
            "max_results": 3,
            "search_query": "'fruit'",
        },
        user,
    )
    service = ServiceHandler().create_service(service_type, **values)
    assert service.search_field_ids == [notes.id]
    assert service.included_field_ids == [name.id]
    exported = service_type.export_prepared_values(service)
    assert exported["search_field_ids"] == [notes.id]
    assert exported["included_field_ids"] == [name.id]

    # Switching tables forgets the field selection.
    new_values = service_type.prepare_values(
        {"table_id": other_table.id}, user, instance=service
    )
    assert new_values["search_field_ids"] == []
    assert new_values["included_field_ids"] == []


@pytest.mark.django_db
def test_vector_search_service_dispatches_matching_rows(setup):
    user, table, name, notes, rows, integration, service_type = setup
    values = service_type.prepare_values(
        {
            "table_id": table.id,
            "integration_id": integration.id,
            "search_field_ids": [notes.id],
            "included_field_ids": [name.id],
            "max_results": 1,
            "search_query": "'fruit'",
        },
        user,
    )
    service = ServiceHandler().create_service(service_type, **values)
    dispatch_context = FakeDispatchContext()

    with patch.object(
        SearchHandler,
        "vector_search",
        return_value=[(rows[0].id, 0.93, notes.id), (rows[1].id, 0.21, notes.id)],
    ) as search:
        resolved = service_type.resolve_service_formulas(service, dispatch_context)
        result = service_type.dispatch_transform(
            service_type.dispatch_data(service, resolved, dispatch_context)
        )

    assert [field.id for field in search.call_args.args[1]] == [notes.id]
    assert search.call_args.args[2] == "fruit"
    assert search.call_args.kwargs["limit"] == 2
    assert result.data == {
        "results": [
            {
                "id": rows[0].id,
                "Name": "Apple",
                "score": 0.93,
                "matched_field": "Notes",
            }
        ],
        "count": 1,
    }


@pytest.mark.django_db
def test_vector_search_service_needs_a_searchable_field(setup):
    user, table, name, notes, rows, integration, service_type = setup
    values = service_type.prepare_values(
        {"table_id": table.id, "integration_id": integration.id}, user
    )
    service = ServiceHandler().create_service(service_type, **values)
    # Without a selection every field with vector search enabled is searched.
    assert [field.id for field in service_type.get_fields_to_search(service)] == [
        notes.id
    ]

    FieldHandler().update_field(user, notes, vector_search_enabled=False)
    with pytest.raises(ServiceImproperlyConfiguredDispatchException):
        service_type.resolve_service_formulas(service, FakeDispatchContext())


def _create_service(setup):
    user, table, name, notes, rows, integration, service_type = setup
    values = service_type.prepare_values(
        {
            "table_id": table.id,
            "integration_id": integration.id,
            "search_field_ids": [notes.id],
            "included_field_ids": [name.id],
            "search_query": "'fruit'",
        },
        user,
    )
    return ServiceHandler().create_service(service_type, **values)


def _reimport(service_type, service, id_mapping, **config):
    exported = service_type.export_serialized(service)
    return service_type.import_serialized(
        service.integration,
        exported,
        id_mapping,
        import_export_config=ImportExportConfig(
            include_permission_data=False, **config
        ),
    )


@pytest.mark.django_db
def test_vector_search_service_import_drops_unmapped_fields(setup, data_fixture):
    user, table, name, notes, rows, integration, service_type = setup
    service = _create_service(setup)

    # A template was written on another installation: its field ids are
    # collisions, not references, and keeping them would break the import.
    imported = _reimport(
        service_type,
        service,
        {"database_fields": {}},
        is_duplicate=True,
        is_template=True,
    )
    assert imported.search_field_ids == []
    assert imported.included_field_ids == []

    # An import into another workspace that only mapped some of the fields.
    other_name = data_fixture.create_text_field(table=table)
    imported = _reimport(
        service_type, service, {"database_fields": {name.id: other_name.id}}
    )
    assert imported.search_field_ids == []
    assert imported.included_field_ids == [other_name.id]


@pytest.mark.django_db
def test_vector_search_service_duplicate_keeps_unmapped_fields(setup):
    user, table, name, notes, rows, integration, service_type = setup
    service = _create_service(setup)

    imported = _reimport(
        service_type, service, {"database_fields": {}}, is_duplicate=True
    )
    assert imported.search_field_ids == [notes.id]
    assert imported.included_field_ids == [name.id]


@pytest.mark.django_db
def test_vector_search_service_needs_a_field_that_is_not_trashed(setup):
    user, table, name, notes, rows, integration, service_type = setup
    service = _create_service(setup)

    FieldHandler().delete_field(user, notes)
    service = service_type.model_class.objects.get(id=service.id)
    with pytest.raises(ServiceImproperlyConfiguredDispatchException):
        service_type.resolve_service_formulas(service, FakeDispatchContext())


@pytest.mark.django_db
def test_vector_search_service_reports_an_unavailable_embeddings_service(setup):
    user, table, name, notes, rows, integration, service_type = setup
    service = _create_service(setup)

    with patch.object(
        SearchHandler,
        "vector_search",
        side_effect=EmbeddingsServiceError("The embeddings service is unavailable."),
    ):
        with pytest.raises(UnexpectedDispatchException) as exc_info:
            service_type.dispatch_data(
                service, {"search_query": "fruit"}, FakeDispatchContext()
            )
    assert str(exc_info.value) == "The embeddings service is unavailable."


@pytest.mark.django_db
def test_vector_search_service_searches_every_field_when_none_are_chosen(setup):
    from tests.baserow.contrib.database.search.test_vector_search import (
        fake_embedder,
    )

    user, table, name, notes, rows, integration, service_type = setup
    with override_settings(BASEROW_EMBEDDINGS_API_URL="http://embeddings.test"):
        title = FieldHandler().create_field(
            user, table, "text", name="Title", vector_search_enabled=True
        )
    RowHandler().update_rows(
        user,
        table,
        [
            {"id": rows[0].id, f"field_{title.id}": "Red"},
            {"id": rows[1].id, f"field_{title.id}": "Fruit delivery"},
        ],
    )
    SearchHandler.update_search_data(table)
    SearchHandler.update_embeddings(table, [title.id, notes.id], embedder=fake_embedder)
    values = service_type.prepare_values(
        {
            "table_id": table.id,
            "integration_id": integration.id,
            "included_field_ids": [name.id],
            "max_results": 5,
            "search_query": "'fruit'",
        },
        user,
    )
    service = ServiceHandler().create_service(service_type, **values)

    # Only the embeddings service is replaced; the search runs for real.
    with (
        override_settings(BASEROW_EMBEDDINGS_API_URL="http://embeddings.test"),
        patch(
            "baserow.contrib.database.search.handler.get_embedder",
            return_value=fake_embedder,
        ),
    ):
        result = ServiceHandler().dispatch_service(service, FakeDispatchContext())

    matched = {row["Name"]: row["matched_field"] for row in result.data["results"]}
    # "A fruit" in Notes and "Fruit delivery" in Title both match.
    assert matched == {"Apple": "Notes", "Truck": "Title"}


@pytest.mark.django_db
def test_vector_search_service_never_widens_when_its_chosen_fields_are_gone(
    setup, data_fixture
):
    from baserow.core.trash.handler import TrashHandler

    user, table, name, notes, rows, integration, service_type = setup
    with override_settings(BASEROW_EMBEDDINGS_API_URL="http://embeddings.test"):
        secret = FieldHandler().create_field(
            user, table, "long_text", name="Secret", vector_search_enabled=True
        )
    service = _create_service(setup)
    assert service.search_all_fields is False

    FieldHandler().delete_field(user, notes)
    TrashHandler.permanently_delete(notes)
    FieldHandler().delete_field(user, name)
    TrashHandler.permanently_delete(name)
    service = service_type.model_class.objects.get(id=service.id)

    # The builder left `Secret` out: it's never searched or returned instead.
    assert service.search_field_ids == []
    with pytest.raises(ServiceImproperlyConfiguredDispatchException):
        service_type.get_fields_to_search(service)
    with pytest.raises(ServiceImproperlyConfiguredDispatchException):
        service_type.get_fields_to_return(service)
    assert secret.id not in [
        field.id
        for field in service_type.model_class.objects.get(
            id=service.id
        ).search_fields.all()
    ]

    # Clearing the selection is the way to search everything again.
    values = service_type.prepare_values(
        {"search_field_ids": [], "included_field_ids": []}, user, instance=service
    )
    assert values["search_all_fields"] is True
    assert values["include_all_fields"] is True


@pytest.mark.django_db
def test_vector_search_service_edits_drop_stale_chosen_fields(setup, data_fixture):
    user, table, name, notes, rows, integration, service_type = setup
    with override_settings(BASEROW_EMBEDDINGS_API_URL="http://embeddings.test"):
        title = FieldHandler().create_field(
            user, table, "text", name="Title", vector_search_enabled=True
        )
        summary = FieldHandler().create_field(
            user, table, "text", name="Summary", vector_search_enabled=True
        )
    values = service_type.prepare_values(
        {
            "table_id": table.id,
            "integration_id": integration.id,
            "search_field_ids": [notes.id, title.id],
        },
        user,
    )
    service = ServiceHandler().create_service(service_type, **values)
    FieldHandler().delete_field(user, notes)
    FieldHandler().update_field(user, title, vector_search_enabled=False)

    # The form still sends the stale ids along with the new choice.
    values = service_type.prepare_values(
        {"search_field_ids": [notes.id, title.id, summary.id]},
        user,
        instance=service,
    )

    assert values["search_field_ids"] == [summary.id]
    assert values["search_all_fields"] is False
