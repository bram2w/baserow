from unittest.mock import MagicMock

import pytest

from baserow.contrib.builder.data_providers.data_provider_types import (
    DataSourceDataProviderType,
    PageParameterDataProviderType,
)
from baserow.contrib.builder.data_providers.registries import (
    builder_data_provider_type_registry,
)
from baserow.core.formula.runtime_formula_context import RuntimeFormulaContext
from baserow.core.services.exceptions import ServiceImproperlyConfigured


def test_page_parameter_data_provider_get_data_chunk():
    page_parameter_provider = PageParameterDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {"page_parameter": {"id": 42}}

    runtime_formula_context = MagicMock()
    runtime_formula_context.application_context = {"request": fake_request}

    assert page_parameter_provider.get_data_chunk(runtime_formula_context, ["id"]) == 42
    assert page_parameter_provider.get_data_chunk(runtime_formula_context, []) is None
    assert (
        page_parameter_provider.get_data_chunk(runtime_formula_context, ["id", "test"])
        is None
    )
    assert (
        page_parameter_provider.get_data_chunk(runtime_formula_context, ["test"])
        is None
    )


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
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        table=table,
        row_id="2",
        name="Item",
    )

    data_source_provider = DataSourceDataProviderType()

    fake_request = MagicMock()

    runtime_formula_context = MagicMock()
    runtime_formula_context.application_context = {
        "request": fake_request,
        "service": data_source.service,
        "page": page,
        "integrations": [integration],
    }
    runtime_formula_context.cache = {}

    assert (
        data_source_provider.get_data_chunk(
            runtime_formula_context, ["Item", "My Color"]
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
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
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

    runtime_formula_context = RuntimeFormulaContext(
        builder_data_provider_type_registry,
        service=data_source.service,
        request=fake_request,
        page=page,
    )

    assert (
        data_source_provider.get_data_chunk(
            runtime_formula_context, ["Item", "My Color"]
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
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        table=table,
        row_id="get('data_source.Id source.Id')",
        name="Item",
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        table=table2,
        row_id="get('page_parameter.id')",
        name="Id source",
    )

    data_source_provider = DataSourceDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {
        "data_source": {"page_id": page.id},
        "page_parameter": {"id": 2},
    }

    runtime_formula_context = RuntimeFormulaContext(
        builder_data_provider_type_registry,
        service=data_source.service,
        request=fake_request,
        page=page,
    )

    assert (
        data_source_provider.get_data_chunk(
            runtime_formula_context, ["Item", "My Color"]
        )
        == "Orange"
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
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        table=table,
        row_id="get('data_source.Blop.Id')",
        name="Item",
    )

    data_source_provider = DataSourceDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {
        "data_source": {"page_id": page.id},
        "page_parameter": {},
    }

    runtime_formula_context = RuntimeFormulaContext(
        builder_data_provider_type_registry,
        service=data_source.service,
        request=fake_request,
        page=page,
    )

    with pytest.raises(ServiceImproperlyConfigured):
        data_source_provider.get_data_chunk(
            runtime_formula_context, ["Item", "My Color"]
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
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        table=table,
        row_id="get('data_source.Item.Id')",
        name="Item",
    )

    data_source_provider = DataSourceDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {
        "data_source": {"page_id": page.id},
        "page_parameter": {},
    }

    runtime_formula_context = RuntimeFormulaContext(
        builder_data_provider_type_registry,
        service=data_source.service,
        request=fake_request,
        page=page,
    )

    with pytest.raises(ServiceImproperlyConfigured):
        data_source_provider.get_data_chunk(
            runtime_formula_context, ["Item", "My Color"]
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
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        table=table,
        row_id="get('data_source.Id source.Id')",
        name="Item",
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=integration,
        table=table2,
        row_id="get('data_source.Item.Id')",
        name="Id source",
    )

    data_source_provider = DataSourceDataProviderType()

    fake_request = MagicMock()
    fake_request.data = {
        "data_source": {"page_id": page.id},
        "page_parameter": {},
    }

    runtime_formula_context = RuntimeFormulaContext(
        builder_data_provider_type_registry,
        service=data_source.service,
        request=fake_request,
        page=page,
    )

    with pytest.raises(ServiceImproperlyConfigured):
        data_source_provider.get_data_chunk(
            runtime_formula_context, ["Item", "My Color"]
        )
