from collections import defaultdict
from unittest.mock import MagicMock

from django.contrib.auth.models import AnonymousUser

import pytest

from baserow.contrib.builder.data_providers.data_provider_types import (
    DataSourceDataProviderType,
    FormDataProviderType,
    PageParameterDataProviderType,
    UserDataProviderType,
)
from baserow.contrib.builder.data_sources.builder_dispatch_context import (
    BuilderDispatchContext,
)
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.formula_importer import import_formula
from baserow.core.services.dispatch_context import DispatchContext
from baserow.core.services.exceptions import ServiceImproperlyConfigured
from baserow.core.user_sources.user_source_user import UserSourceUser
from baserow.core.utils import MirrorDict


class FakeDispatchContext(DispatchContext):
    def __init__():
        super().__init__()

    def range(self, service):
        return [0, 100]

    def __getitem__(self, key: str):
        if key == "test":
            return 2
        if key == "test1":
            return 1
        if key == "test2":
            return ""
        if key == "test999":
            return "999"

        return super().__getitem__(key)


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


def test_form_data_provider_get_data_chunk():
    form_data_provider = FormDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {"form_data": {"1": {"value": "hello"}}}

    dispatch_context = BuilderDispatchContext(fake_request, None)

    assert form_data_provider.get_data_chunk(dispatch_context, ["1"]) == "hello"
    assert form_data_provider.get_data_chunk(dispatch_context, []) is None
    assert form_data_provider.get_data_chunk(dispatch_context, ["1", "test"]) is None
    assert form_data_provider.get_data_chunk(dispatch_context, ["test"]) is None


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

    fake_request = MagicMock()

    dispatch_context = BuilderDispatchContext(fake_request, page)

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

    fake_request = MagicMock()
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

    fake_request = MagicMock()
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

    fake_request = MagicMock()
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

    fake_request = MagicMock()
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

    fake_request = MagicMock()
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

    fake_request = MagicMock()
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
        None, None, 42, "username", "e@ma.il"
    )

    assert user_data_provider_type.get_data_chunk(
        dispatch_context, ["is_authenticated"]
    )
    assert (
        user_data_provider_type.get_data_chunk(dispatch_context, ["email"]) == "e@ma.il"
    )
    assert user_data_provider_type.get_data_chunk(dispatch_context, ["id"]) == 42
