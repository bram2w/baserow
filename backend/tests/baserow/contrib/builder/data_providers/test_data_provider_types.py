from collections import defaultdict
from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

import pytest

from baserow.contrib.builder.data_providers.data_provider_types import (
    CurrentRecordDataProviderType,
    DataSourceContextDataProviderType,
    DataSourceDataProviderType,
    FormDataProviderType,
    PageParameterDataProviderType,
    PreviousActionProviderType,
    UserDataProviderType,
)
from baserow.contrib.builder.data_providers.exceptions import (
    DataProviderChunkInvalidException,
    FormDataProviderChunkInvalidException,
)
from baserow.contrib.builder.data_sources.builder_dispatch_context import (
    BuilderDispatchContext,
)
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.formula_importer import import_formula
from baserow.contrib.builder.workflow_actions.models import EventTypes
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.core.services.exceptions import ServiceImproperlyConfigured
from baserow.core.user_sources.constants import DEFAULT_USER_ROLE_PREFIX
from baserow.core.user_sources.user_source_user import UserSourceUser
from baserow.core.utils import MirrorDict


def test_page_parameter_data_provider_get_data_chunk():
    page_parameter_provider = PageParameterDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {"page_parameter": {"id": 42}}

    dispatch_context = BuilderDispatchContext(fake_request, None)

    assert page_parameter_provider.get_data_chunk(dispatch_context, ["id"]) == 42
    assert page_parameter_provider.get_data_chunk(dispatch_context, []) is None
    assert (
        page_parameter_provider.get_data_chunk(dispatch_context, ["id", "test"]) is None
    )
    assert page_parameter_provider.get_data_chunk(dispatch_context, ["test"]) is None


@patch(
    "baserow.contrib.builder.data_providers.data_provider_types.FormDataProviderType.validate_data_chunk"
)
def test_form_data_provider_get_data_chunk(mock_validate):
    form_data_provider = FormDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {"form_data": {"1": "hello", "2": ["a", "b"]}}

    dispatch_context = BuilderDispatchContext(fake_request, None)
    mock_validate.side_effect = lambda x, y, z: y

    # A single valued form data
    assert form_data_provider.get_data_chunk(dispatch_context, ["1"]) == "hello"
    # A multiple valued form data
    assert form_data_provider.get_data_chunk(dispatch_context, ["2", "*"]) == ["a", "b"]
    # A multiple valued form data at a specific index
    assert form_data_provider.get_data_chunk(dispatch_context, ["2", "0"]) == "a"
    # Paths longer than 2 are unsupported.
    assert form_data_provider.get_data_chunk(dispatch_context, ["2", "*", "z"]) is None
    # Unknown form data fields are None
    assert form_data_provider.get_data_chunk(dispatch_context, ["3"]) is None
    # Empty paths are None
    assert form_data_provider.get_data_chunk(dispatch_context, []) is None


@patch("baserow.contrib.builder.data_providers.data_provider_types.ElementHandler")
def test_form_data_provider_validate_data_chunk(mock_handler):
    mock_element = Mock()
    mock_element_type = Mock()

    mock_element.get_type.return_value = mock_element_type
    mock_handler().get_element.return_value = mock_element

    form_data_provider = FormDataProviderType()

    mock_element_type.is_valid.return_value = "something"
    assert form_data_provider.validate_data_chunk("1", "horse", {}) == "something"

    def raise_exc(x, y, z):
        raise FormDataProviderChunkInvalidException()

    mock_element_type.is_valid.side_effect = raise_exc
    with pytest.raises(FormDataProviderChunkInvalidException) as exc:
        assert form_data_provider.validate_data_chunk("1", 42, {})

    assert exc.value.args[0].startswith("Provided value for form element with ID")


@pytest.mark.django_db
def test_data_source_data_provider_get_data_chunk(data_fixture):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
            ["Volkswagen", "White"],
            ["Volkswagen", "Green"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="2",
        name="Item",
    )

    data_source_provider = DataSourceDataProviderType()

    dispatch_context = BuilderDispatchContext(HttpRequest(), page)

    assert (
        data_source_provider.get_data_chunk(
            dispatch_context, [data_source.id, fields[1].db_column]
        )
        == "Orange"
    )


@pytest.mark.django_db
def test_data_source_data_provider_get_data_chunk_with_formula(data_fixture):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
            ["Volkswagen", "White"],
            ["Volkswagen", "Green"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="get('page_parameter.id')",
        name="Item",
    )

    data_source_provider = DataSourceDataProviderType()

    fake_request = HttpRequest()
    fake_request.data = {
        "data_source": {"page_id": page.id},
        "page_parameter": {"id": 2},
    }

    dispatch_context = BuilderDispatchContext(fake_request, page)

    assert (
        data_source_provider.get_data_chunk(
            dispatch_context, [data_source.id, fields[1].db_column]
        )
        == "Orange"
    )


@pytest.mark.django_db
def test_data_source_data_provider_get_data_chunk_with_formula_using_datasource(
    data_fixture,
):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
            ["Volkswagen", "White"],
            ["Volkswagen", "Green"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    table2, fields2, rows2 = data_fixture.build_table(
        user=user,
        columns=[
            ("Id", "text"),
        ],
        rows=[
            ["1"],
            ["2"],
            ["3"],
            ["3"],
        ],
    )
    view2 = data_fixture.create_grid_view(user, table=table2)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view2,
        table=table2,
        row_id="get('page_parameter.id')",
        name="Id source",
    )
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id=f"get('data_source.{data_source2.id}.{fields2[0].db_column}')",
        name="Item",
    )

    data_source_provider = DataSourceDataProviderType()

    fake_request = HttpRequest()
    fake_request.data = {
        "data_source": {"page_id": page.id},
        "page_parameter": {"id": 2},
    }

    dispatch_context = BuilderDispatchContext(fake_request, page)

    assert (
        data_source_provider.get_data_chunk(
            dispatch_context, [data_source.id, fields[1].db_column]
        )
        == "Orange"
    )


@pytest.mark.django_db
def test_data_source_data_provider_get_data_chunk_with_formula_using_list_datasource(
    data_fixture,
):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
            ["Volkswagen", "White"],
            ["Volkswagen", "Green"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    table2, fields2, rows2 = data_fixture.build_table(
        user=user,
        columns=[
            ("Id", "text"),
        ],
        rows=[
            ["1"],
            ["2"],
            ["3"],
            ["3"],
        ],
    )
    view2 = data_fixture.create_grid_view(user, table=table2)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source2 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view2,
        table=table2,
        name="List source",
    )
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id=f"get('data_source.{data_source2.id}.2.{fields2[0].db_column}')",
        name="Item",
    )

    data_source_provider = DataSourceDataProviderType()

    fake_request = HttpRequest()
    fake_request.data = {
        "data_source": {"page_id": page.id},
        "page_parameter": {"id": 2},
    }
    fake_request.GET = {"count": 20}

    dispatch_context = BuilderDispatchContext(fake_request, page)

    assert (
        data_source_provider.get_data_chunk(
            dispatch_context, [data_source.id, fields[1].db_column]
        )
        == "White"
    )


@pytest.mark.django_db
def test_data_source_data_provider_get_data_chunk_with_formula_to_missing_datasource(
    data_fixture,
):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
            ["Volkswagen", "White"],
            ["Volkswagen", "Green"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    table2, fields2, rows2 = data_fixture.build_table(
        user=user,
        columns=[
            ("Id", "text"),
        ],
        rows=[
            ["1"],
            ["2"],
            ["3"],
            ["3"],
        ],
    )
    view2 = data_fixture.create_grid_view(user, table=table2)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="get('data_source.99999.Id')",
        name="Item",
    )

    data_source_provider = DataSourceDataProviderType()

    fake_request = HttpRequest()
    fake_request.data = {
        "data_source": {"page_id": page.id},
        "page_parameter": {},
    }

    dispatch_context = BuilderDispatchContext(fake_request, page)

    with pytest.raises(ServiceImproperlyConfigured):
        data_source_provider.get_data_chunk(
            dispatch_context, [data_source.id, fields[1].db_column]
        )


@pytest.mark.django_db
def test_data_source_data_provider_get_data_chunk_with_formula_recursion(
    data_fixture,
):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
            ["Volkswagen", "White"],
            ["Volkswagen", "Green"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    table2, fields2, rows2 = data_fixture.build_table(
        user=user,
        columns=[
            ("Id", "text"),
        ],
        rows=[
            ["1"],
            ["2"],
            ["3"],
            ["3"],
        ],
    )
    view2 = data_fixture.create_grid_view(user, table=table2)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="",
        name="Item",
    )

    data_source.row_id = f"get('data_source.{data_source.id}.Id')"
    data_source.save()

    data_source_provider = DataSourceDataProviderType()

    fake_request = HttpRequest()
    fake_request.data = {
        "data_source": {"page_id": page.id},
        "page_parameter": {},
    }

    dispatch_context = BuilderDispatchContext(fake_request, page)

    assert (
        data_source_provider.get_data_chunk(
            dispatch_context, [data_source.id, fields[1].db_column]
        )
        == "Blue"
    )


@pytest.mark.django_db
def test_data_source_data_provider_get_data_chunk_with_formula_using_datasource_calling_each_others(
    data_fixture,
):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
            ["Volkswagen", "White"],
            ["Volkswagen", "Green"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    table2, fields2, rows2 = data_fixture.build_table(
        user=user,
        columns=[
            ("Id", "text"),
        ],
        rows=[
            ["1"],
            ["2"],
            ["3"],
            ["3"],
        ],
    )
    view2 = data_fixture.create_grid_view(user, table=table2)
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view,
        table=table,
        row_id="",
        name="Item",
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        view=view2,
        table=table2,
        row_id=f"get('data_source.{data_source.id}.Id')",
        name="Id source",
    )

    data_source.row_id = f"get('data_source.{data_source2.id}.Id')"
    data_source.save()

    data_source_provider = DataSourceDataProviderType()

    fake_request = HttpRequest()
    fake_request.data = {
        "data_source": {"page_id": page.id},
        "page_parameter": {},
    }

    dispatch_context = BuilderDispatchContext(fake_request, page)

    assert (
        data_source_provider.get_data_chunk(
            dispatch_context, [data_source.id, fields[1].db_column]
        )
        == "Blue"
    )


@pytest.mark.django_db
def test_data_source_formula_import_only_datasource(data_fixture):
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        row_id="",
        name="Item",
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        row_id="",
        name="Item",
    )

    id_mapping = defaultdict(lambda: MirrorDict())
    id_mapping["builder_data_sources"] = {data_source.id: data_source2.id}

    result = import_formula(f"get('data_source.{data_source.id}.field_10')", id_mapping)

    assert result == f"get('data_source.{data_source2.id}.field_10')"


@pytest.mark.django_db
def test_data_source_formula_import_get_row_datasource_and_field(data_fixture):
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        row_id="",
        name="Item",
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        row_id="",
        name="Item",
    )
    field_1 = data_fixture.create_text_field(order=1)
    field_2 = data_fixture.create_text_field(order=2)

    id_mapping = defaultdict(lambda: MirrorDict())
    id_mapping["builder_data_sources"] = {data_source.id: data_source2.id}
    id_mapping["database_fields"] = {field_1.id: field_2.id}

    result = import_formula(
        f"get('data_source.{data_source.id}.field_{field_1.id}')", id_mapping
    )

    assert result == f"get('data_source.{data_source2.id}.field_{field_2.id}')"


@pytest.mark.django_db
def test_data_source_formula_import_list_row_datasource_and_field(data_fixture):
    data_source = data_fixture.create_builder_local_baserow_list_rows_data_source(
        name="Item",
    )
    data_source2 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        name="Item",
    )
    field_1 = data_fixture.create_text_field(order=1)
    field_2 = data_fixture.create_text_field(order=2)

    id_mapping = defaultdict(lambda: MirrorDict())
    id_mapping["builder_data_sources"] = {data_source.id: data_source2.id}
    id_mapping["database_fields"] = {field_1.id: field_2.id}

    result = import_formula(
        f"get('data_source.{data_source.id}.10.field_{field_1.id}')", id_mapping
    )

    assert result == f"get('data_source.{data_source2.id}.10.field_{field_2.id}')"


@pytest.mark.django_db
def test_data_source_formula_import_missing_get_row_datasource(data_fixture):
    id_mapping = defaultdict(lambda: MirrorDict())
    id_mapping["builder_data_sources"] = {}

    result = import_formula(f"get('data_source.42.field_24')", id_mapping)

    assert result == f"get('data_source.42.field_24')"

    id_mapping["builder_data_sources"] = {42: 42}

    result = import_formula(f"get('data_source.42.field_24')", id_mapping)

    assert result == f"get('data_source.42.field_24')"


@pytest.mark.django_db
def test_data_source_context_data_provider_get_data_chunk(data_fixture):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user, columns=[("Name", "text")], rows=[]
    )
    field_handler = FieldHandler()
    field = field_handler.create_field(
        user=user,
        table=table,
        type_name="single_select",
        name="Category",
        select_options=[
            {
                "value": "Bakery",
                "color": "red",
            },
            {
                "value": "Grocery",
                "color": "green",
            },
        ],
    )
    builder = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        table=table,
        row_id="",
        name="Item",
    )
    data_source_context_provider = DataSourceContextDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {
        "page_parameter": {},
    }
    dispatch_context = BuilderDispatchContext(fake_request, page)

    # For fields that are not single select, `get_data_chunk` returns an empty response
    assert (
        data_source_context_provider.get_data_chunk(
            dispatch_context, [str(data_source.id), fields[0].db_column]
        )
        is None
    )

    # For single select fields, we should be able to select one/all of the options
    assert (
        data_source_context_provider.get_data_chunk(
            dispatch_context, [str(data_source.id), field.db_column, "0", "value"]
        )
        == "Bakery"
    )

    assert data_source_context_provider.get_data_chunk(
        dispatch_context, [str(data_source.id), field.db_column, "*", "value"]
    ) == ["Bakery", "Grocery"]

    assert data_source_context_provider.get_data_chunk(
        dispatch_context, [str(data_source.id), field.db_column, "*", "color"]
    ) == ["red", "green"]


@pytest.mark.django_db
def test_data_source_data_context_data_provider_import_path(data_fixture):
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source()
    data_source_context_provider = DataSourceContextDataProviderType()

    assert data_source_context_provider.import_path(["1"], {}) == ["1"]
    assert data_source_context_provider.import_path(
        ["1"], {"builder_data_sources": {1: 2}}
    ) == ["2"]

    assert data_source_context_provider.import_path(
        ["1"], {"builder_data_sources": {1: data_source.id}}
    ) == [str(data_source.id)]


@pytest.mark.django_db
def test_table_element_formula_migration_with_current_row_provider(data_fixture):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
        ],
    )

    table2, fields2, rows2 = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
        ],
    )

    page = data_fixture.create_builder_page(user=user)

    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page,
        table=table,
    )

    data_source2 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        table=table2,
    )

    id_mapping = defaultdict(lambda: MirrorDict())
    id_mapping["builder_data_sources"] = {data_source.id: data_source2.id}
    id_mapping["database_fields"] = {fields[0].id: fields2[0].id}

    result = import_formula(
        f"get('current_record.field_{fields[0].id}')",
        id_mapping,
        data_source_id=data_source2.id,
    )

    assert result == f"get('current_record.field_{fields2[0].id}')"


@pytest.mark.django_db
def test_form_data_provider_type_import_path(data_fixture):
    element = data_fixture.create_builder_heading_element()
    element_duplicated = ElementHandler().duplicate_element(element)["elements"][0]

    id_mapping = {"builder_page_elements": {element.id: element_duplicated.id}}
    path = [str(element.id), "test"]

    path_imported = FormDataProviderType().import_path(path, id_mapping)

    assert path_imported == [str(element_duplicated.id), "test"]


def test_previous_action_data_provider_get_data_chunk():
    previous_action_data_provider = PreviousActionProviderType()

    fake_request = MagicMock()
    fake_request.data = {"previous_action": {"id": 42}}
    dispatch_context = BuilderDispatchContext(fake_request, None)

    assert previous_action_data_provider.get_data_chunk(dispatch_context, ["id"]) == 42
    with pytest.raises(DataProviderChunkInvalidException):
        previous_action_data_provider.get_data_chunk(dispatch_context, ["invalid"])


@pytest.mark.django_db
def test_previous_action_data_provider_import_path():
    previous_action_data_provider = PreviousActionProviderType()
    path = ["1", "field"]

    valid_id_mapping = {"builder_workflow_actions": {1: 2}}
    invalid_id_mapping = {"builder_workflow_actions": {0: 1}}

    assert previous_action_data_provider.import_path(path, {}) == ["1", "field"]
    assert previous_action_data_provider.import_path(path, invalid_id_mapping) == [
        "1",
        "field",
    ]
    assert previous_action_data_provider.import_path(path, valid_id_mapping) == [
        "2",
        "field",
    ]


@pytest.mark.django_db
def test_user_data_provider_get_data_chunk(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)

    user_data_provider_type = UserDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {
        "page_parameter": {},
    }
    fake_request.user_source_user = AnonymousUser()

    dispatch_context = BuilderDispatchContext(fake_request, page)

    assert not user_data_provider_type.get_data_chunk(
        dispatch_context, ["is_authenticated"]
    )

    assert user_data_provider_type.get_data_chunk(dispatch_context, ["id"]) == 0

    fake_request.user_source_user = UserSourceUser(
        None, None, 42, "username", "e@ma.il", "foo_role"
    )

    assert user_data_provider_type.get_data_chunk(
        dispatch_context, ["is_authenticated"]
    )
    assert (
        user_data_provider_type.get_data_chunk(dispatch_context, ["email"]) == "e@ma.il"
    )
    assert user_data_provider_type.get_data_chunk(dispatch_context, ["id"]) == 42
    assert (
        user_data_provider_type.get_data_chunk(dispatch_context, ["role"]) == "foo_role"
    )


@pytest.mark.django_db
def test_translate_default_user_role_returns_same_role(data_fixture):
    """
    Ensure the UserDataProviderType's get_data_chunk() method returns
    the same User Role.

    When the role is a non-Default User Role, the same role should be returned.
    """

    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    user_data_provider_type = UserDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {
        "page_parameter": {},
    }
    fake_request.user_source_user = AnonymousUser()

    dispatch_context = BuilderDispatchContext(fake_request, page)

    user_role = "foo_role"
    fake_request.user_source_user = UserSourceUser(
        None, None, 42, "username", "e@ma.il", user_role
    )

    assert (
        user_data_provider_type.get_data_chunk(dispatch_context, ["role"]) == user_role
    )


@pytest.mark.django_db
def test_translate_default_user_role_returns_translated_role(data_fixture):
    """
    Ensure the UserDataProviderType's get_data_chunk() method returns
    the translated Default User Role.
    """

    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    user_source_name = "FooUserSource"
    user_source = data_fixture.create_user_source_with_first_type(name=user_source_name)
    default_user_source_name = f"{DEFAULT_USER_ROLE_PREFIX}{user_source.id}"

    user_data_provider_type = UserDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {
        "page_parameter": {},
    }

    dispatch_context = BuilderDispatchContext(fake_request, page)
    fake_request.user_source_user = UserSourceUser(
        user_source, None, 42, "username", "e@ma.il", default_user_source_name
    )

    assert (
        user_data_provider_type.get_data_chunk(dispatch_context, ["role"])
        == f"{user_source_name} member"
    )


@pytest.mark.django_db
def test_current_record_provider_get_data_chunk_without_record_index(data_fixture):
    current_record_provider = CurrentRecordDataProviderType()

    user, token = data_fixture.create_user_and_token()

    fake_request = HttpRequest()
    fake_request.data = {}

    builder = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(user=user, builder=builder)
    workflow_action = data_fixture.create_local_baserow_create_row_workflow_action(
        page=page, event=EventTypes.CLICK, user=user
    )

    dispatch_context = BuilderDispatchContext(fake_request, page, workflow_action)
    assert current_record_provider.get_data_chunk(dispatch_context, ["path"]) is None


@pytest.mark.django_db
def test_current_record_provider_get_data_chunk(data_fixture):
    current_record_provider = CurrentRecordDataProviderType()

    user, token = data_fixture.create_user_and_token()

    fake_request = HttpRequest()
    fake_request.user = user
    fake_request.data = {"current_record": 0}

    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Animal", "text"),
        ],
        rows=[
            ["Badger"],
            ["Horse"],
            ["Bison"],
        ],
    )
    field = table.field_set.get(name="Animal")
    builder = data_fixture.create_builder_application(user=user)
    page = data_fixture.create_builder_page(user=user, builder=builder)

    data_source = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page, table=table, integration_args={"authorized_user": user}
    )
    repeat_element = data_fixture.create_builder_repeat_element(
        page=page, data_source=data_source
    )
    button_element = data_fixture.create_builder_button_element(
        page=page, parent_element=repeat_element
    )

    workflow_action = data_fixture.create_local_baserow_create_row_workflow_action(
        page=page, element=button_element, event=EventTypes.CLICK, user=user
    )

    dispatch_context = BuilderDispatchContext(fake_request, page, workflow_action)

    assert (
        current_record_provider.get_data_chunk(dispatch_context, [field.db_column])
        == "Badger"
    )


@pytest.mark.django_db
def test_current_record_provider_type_import_path(data_fixture):
    # When a `current_record` provider is imported, and the path only contains the
    # current record index (`__idx__`), then there is no need to update the path.
    id_mapping = {"builder_page_elements": {}}
    assert CurrentRecordDataProviderType().import_path(["__idx__"], id_mapping) == [
        "__idx__"
    ]

    data_source = data_fixture.create_builder_local_baserow_list_rows_data_source()
    field_1 = data_fixture.create_text_field(order=1)
    field_2 = data_fixture.create_text_field(order=2)

    id_mapping = defaultdict(lambda: MirrorDict())
    id_mapping["database_fields"] = {field_1.id: field_2.id}

    assert CurrentRecordDataProviderType().import_path(
        [field_1.db_column], id_mapping, data_source_id=data_source.id
    ) == [field_2.db_column]
