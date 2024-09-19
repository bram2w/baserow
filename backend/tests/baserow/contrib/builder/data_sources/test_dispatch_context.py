from unittest.mock import MagicMock

from django.http import HttpRequest

import pytest
from rest_framework.request import Request

from baserow.contrib.builder.data_sources.builder_dispatch_context import (
    BuilderDispatchContext,
)


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
def test_dispatch_context_page_from_context(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    request = Request(HttpRequest())
    request.user = user

    dispatch_context = BuilderDispatchContext(request, page, offset=0, count=5)
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


def test_dispatch_context_search_query():
    request = HttpRequest()
    request.GET["search_query"] = "foobar"
    dispatch_context = BuilderDispatchContext(request, None)
    assert dispatch_context.search_query() == "foobar"


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
