from unittest.mock import MagicMock, patch

from django.http import HttpRequest

import pytest
from rest_framework.request import Request

from baserow.contrib.builder.data_sources.builder_dispatch_context import (
    FEATURE_FLAG_EXCLUDE_UNUSED_FIELDS,
    BuilderDispatchContext,
)
from baserow.contrib.builder.data_sources.exceptions import (
    DataSourceRefinementForbidden,
)
from baserow.core.services.utils import ServiceAdhocRefinements


def test_dispatch_context_page_range():
    request = MagicMock()
    request.GET = {"offset": 42, "count": 42}

    dispatch_context = BuilderDispatchContext(request, None)

    assert dispatch_context.range(None) == [42, 42]

    request.GET = {"offset": "foo", "count": "bar"}

    dispatch_context = BuilderDispatchContext(request, None)

    assert dispatch_context.range(None) == [0, 20]

    request.GET = {"offset": "-20", "count": "-10"}

    dispatch_context = BuilderDispatchContext(request, None)

    assert dispatch_context.range(None) == [0, 1]


@pytest.mark.django_db
@patch(
    "baserow.contrib.builder.data_sources.builder_dispatch_context.get_formula_field_names"
)
def test_dispatch_context_page_from_context(mock_get_field_names, data_fixture):
    mock_get_field_names.return_value = {"all": {}, "external": {}, "internal": {}}

    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    request = Request(HttpRequest())
    request.user = user

    dispatch_context = BuilderDispatchContext(
        request, page, offset=0, count=5, only_expose_public_formula_fields=True
    )
    dispatch_context.annotated_data = "foobar"

    dispatch_context.cache = {"key": "value"}
    new_dispatch_context = BuilderDispatchContext.from_context(
        dispatch_context, offset=5, count=1
    )
    assert getattr(new_dispatch_context, "annotated_data", None) is None
    assert new_dispatch_context.cache == {"key": "value"}
    assert new_dispatch_context.request == request
    assert new_dispatch_context.page == page
    assert new_dispatch_context.offset == 5
    assert new_dispatch_context.count == 1
    assert new_dispatch_context.public_formula_fields == {
        "all": {},
        "external": {},
        "internal": {},
    }


def test_dispatch_context_search_query():
    request = HttpRequest()
    request.GET["search_query"] = "foobar"
    dispatch_context = BuilderDispatchContext(request, None)
    assert dispatch_context.search_query() == "foobar"


@pytest.mark.django_db
def test_dispatch_context_searchable_fields(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    dispatch_context = BuilderDispatchContext(HttpRequest(), page)
    with pytest.raises(DataSourceRefinementForbidden):
        dispatch_context.searchable_fields()
    element = data_fixture.create_builder_table_element(page=page)
    element.property_options.create(schema_property="name", searchable=True)
    element.property_options.create(schema_property="location", searchable=True)
    element.property_options.create(schema_property="top_secret", searchable=False)
    dispatch_context = BuilderDispatchContext(HttpRequest(), page, element=element)
    assert dispatch_context.searchable_fields() == ["name", "location"]


def test_dispatch_context_filters():
    request = HttpRequest()
    filter_data = {
        "groups": [],
        "filter_type": "AND",
        "filters": [
            {
                "field": 123,
                "type": "contains",
                "value": "Alexa",
            }
        ],
    }
    request.GET["filters"] = filter_data
    dispatch_context = BuilderDispatchContext(request, None)
    assert dispatch_context.filters() == filter_data


def test_dispatch_context_sortings():
    request = HttpRequest()
    request.GET["order_by"] = "-field_1,-field_2"
    dispatch_context = BuilderDispatchContext(request, None)
    assert dispatch_context.sortings() == "-field_1,-field_2"


@pytest.mark.parametrize(
    "feature_flag_is_set,only_expose_public_formula_fields",
    (
        [False, True],
        [True, True],
        [False, False],
        [True, False],
    ),
)
@patch(
    "baserow.contrib.builder.data_sources.builder_dispatch_context.get_formula_field_names"
)
@patch(
    "baserow.contrib.builder.data_sources.builder_dispatch_context.feature_flag_is_enabled"
)
def test_builder_dispatch_context_field_names_computed_on_feature_flag(
    mock_feature_flag_is_enabled,
    mock_get_formula_field_names,
    feature_flag_is_set,
    only_expose_public_formula_fields,
):
    """
    Test the BuilderDispatchContext::field_names property.

    Ensure that the field_names property is computed only when the feature
    flag is on.
    """

    mock_feature_flag_is_enabled.return_value = True if feature_flag_is_set else False

    mock_field_names = MagicMock()
    mock_get_formula_field_names.return_value = mock_field_names

    mock_request = MagicMock()
    mock_page = MagicMock()

    dispatch_context = BuilderDispatchContext(
        mock_request,
        mock_page,
        only_expose_public_formula_fields=only_expose_public_formula_fields,
    )

    if feature_flag_is_set and only_expose_public_formula_fields:
        assert dispatch_context.public_formula_fields == mock_field_names
        mock_get_formula_field_names.assert_called_once_with(
            mock_request.user, mock_page
        )
        mock_feature_flag_is_enabled.assert_called_once_with(
            FEATURE_FLAG_EXCLUDE_UNUSED_FIELDS
        )
    else:
        assert dispatch_context.public_formula_fields is None
        mock_get_formula_field_names.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "property_option_params",
    [
        {
            "schema_property": "name",
            "filterable": True,
            "sortable": False,
            "searchable": False,
        },
        {
            "schema_property": "age",
            "filterable": False,
            "sortable": True,
            "searchable": False,
        },
        {
            "schema_property": "location",
            "filterable": False,
            "sortable": False,
            "searchable": True,
        },
    ],
)
def test_validate_filter_search_sort_fields(data_fixture, property_option_params):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    element = data_fixture.create_builder_table_element(page=page)
    element.property_options.create(**property_option_params)
    dispatch_context = BuilderDispatchContext(HttpRequest(), page, element=element)
    schema_property = property_option_params["schema_property"]
    for refinement in list(ServiceAdhocRefinements):
        model_field_name = ServiceAdhocRefinements.to_model_field(refinement)
        if property_option_params[model_field_name]:
            dispatch_context.validate_filter_search_sort_fields(
                [schema_property], refinement
            )
        else:
            with pytest.raises(DataSourceRefinementForbidden) as exc:
                dispatch_context.validate_filter_search_sort_fields(
                    [schema_property], refinement
                )
            assert (
                exc.value.args[0]
                == f"{schema_property} is not a {model_field_name} field."
            )


@pytest.mark.django_db
def test_get_element_property_options(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    element = data_fixture.create_builder_table_element(page=page)
    element.property_options.create(
        schema_property="name", filterable=True, sortable=False, searchable=False
    )
    dispatch_context = BuilderDispatchContext(HttpRequest(), page, element=element)
    assert dispatch_context.cache == {}
    with django_assert_num_queries(1):
        dispatch_context.get_element_property_options()
    assert dispatch_context.cache["element_property_options"] == {
        "name": {"filterable": True, "sortable": False, "searchable": False}
    }
    with django_assert_num_queries(0):
        dispatch_context.get_element_property_options()


def test_validate_filter_search_sort_fields_without_element():
    dispatch_context = BuilderDispatchContext(HttpRequest(), None)
    with pytest.raises(DataSourceRefinementForbidden) as exc:
        dispatch_context.validate_filter_search_sort_fields(
            ["name"], ServiceAdhocRefinements.FILTER
        )
    assert (
        exc.value.args[0]
        == "An element is required to validate filter, search and sort fields."
    )
