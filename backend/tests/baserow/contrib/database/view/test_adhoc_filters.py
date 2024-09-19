import json

from django.http import HttpRequest

import pytest

from baserow.contrib.database.api.views.exceptions import (
    FiltersParamValidationException,
)
from baserow.contrib.database.fields.field_filters import FILTER_TYPE_OR
from baserow.contrib.database.views.filters import AdHocFilters


def test_adhoc_filters_from_request():
    request = HttpRequest()
    filters = {
        "groups": [],
        "filter_type": "OR",  # grouped filtering filter_type
        "filters": [
            {
                "field": 123,
                "type": "contains",
                "value": "foobar",
            },
        ],
    }
    request.GET["filter_type"] = "OR"  # simple filtering filter_type
    request.GET["filters"] = json.dumps(filters)
    adhoc_filters = AdHocFilters.from_request(request)
    assert adhoc_filters.api_filters == filters
    assert adhoc_filters.filter_type == FILTER_TYPE_OR

    filters_with_invalid_character = {
        "filter_type": "AND",
        "filters": [
            {"field": 456, "type": "contains", "value": "a\0"},
        ],
    }
    request.GET["filters"] = json.dumps(filters_with_invalid_character)
    adhoc_filters = AdHocFilters.from_request(request)
    assert adhoc_filters.api_filters["filters"][0]["value"] == "a"


def test_adhoc_filters_from_dict():
    data = {
        "groups": [],
        "filter_type": "OR",  # grouped filtering filter_type
        "filters": [
            {
                "field": 123,
                "type": "contains",
                "value": "foobar",
            },
        ],
    }
    adhoc_filters = AdHocFilters.from_dict(data)
    assert adhoc_filters.api_filters == data
    assert adhoc_filters.filter_type == FILTER_TYPE_OR

    filters_with_invalid_character = {
        "filter_type": "AND",
        "filters": [
            {"field": 456, "type": "contains", "value": "a\0"},
        ],
    }
    adhoc_filters = AdHocFilters.from_dict(filters_with_invalid_character)
    assert adhoc_filters.api_filters["filters"][0]["value"] == "a"


def test_deserialize_dispatch_filters():
    filters = {
        "groups": [],
        "filter_type": "OR",
        "filters": [
            {
                "field": 123,
                "type": "contains",
                "value": "foobar",
            },
        ],
    }
    serialized_filters = json.dumps(filters)
    assert AdHocFilters.deserialize_dispatch_filters(serialized_filters) == filters
    with pytest.raises(FiltersParamValidationException):
        AdHocFilters.deserialize_dispatch_filters("{invalid]")
