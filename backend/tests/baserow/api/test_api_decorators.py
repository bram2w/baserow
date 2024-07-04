import json
import zoneinfo
from datetime import timezone
from unittest.mock import MagicMock

from django.db import OperationalError

import pytest
from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.test import APIRequestFactory

from baserow.api.decorators import (
    accept_timezone,
    allowed_includes,
    map_exceptions,
    require_request_data_type,
    validate_body,
    validate_body_custom_fields,
    validate_query_parameters,
)
from baserow.api.exceptions import (
    QueryParameterValidationException,
    RequestBodyValidationException,
)
from baserow.core.exceptions import PermissionDenied
from baserow.core.models import Workspace
from baserow.core.registry import (
    CustomFieldsInstanceMixin,
    Instance,
    ModelInstanceMixin,
    Registry,
)


class TemporaryException(Exception):
    pass


class TemporarySerializer(serializers.Serializer):
    field_1 = serializers.CharField()
    field_2 = serializers.ChoiceField(choices=("choice_1", "choice_2"))


class TemporaryQueryParamSerializer(serializers.Serializer):
    field_3 = serializers.IntegerField(required=True)


class TemporaryBaseModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("name",)


class TemporaryInstance(CustomFieldsInstanceMixin, ModelInstanceMixin, Instance):
    pass


class TemporaryInstanceType1(TemporaryInstance):
    type = "temporary_1"
    model_class = Workspace


class TemporaryInstanceType2(TemporaryInstance):
    type = "temporary_2"
    model_class = Workspace
    serializer_field_names = ["name"]
    serializer_field_overrides = {"name": serializers.IntegerField()}


class TemporaryTypeRegistry(Registry):
    name = "temporary"


def test_map_exceptions_decorator():
    @map_exceptions({TemporaryException: "ERROR_TEMPORARY"})
    def test_1():
        raise TemporaryException

    with pytest.raises(APIException) as api_exception_1:
        test_1()

    assert api_exception_1.value.detail["error"] == "ERROR_TEMPORARY"
    assert api_exception_1.value.detail["detail"] == ""
    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST

    @map_exceptions(
        {
            TemporaryException: (
                "ERROR_TEMPORARY_2",
                HTTP_404_NOT_FOUND,
                "Another message",
            )
        }
    )
    def test_2():
        raise TemporaryException

    with pytest.raises(APIException) as api_exception_2:
        test_2()

    assert api_exception_2.value.detail["error"] == "ERROR_TEMPORARY_2"
    assert api_exception_2.value.detail["detail"] == "Another message"
    assert api_exception_2.value.status_code == status.HTTP_404_NOT_FOUND

    @map_exceptions({TemporaryException: "ERROR_TEMPORARY_3"})
    def test_3():
        pass

    test_3()

    # Calling the decorator with no `exceptions` dict
    # still includes the `PermissionDenied` exception.
    @map_exceptions()
    def test_no_dict():
        raise PermissionDenied()

    with pytest.raises(APIException) as exc_permissiondenied:
        test_no_dict()

    assert exc_permissiondenied.value.detail["error"] == "PERMISSION_DENIED"
    assert (
        exc_permissiondenied.value.detail["detail"]
        == "You don't have the required permission to execute this operation."
    )
    assert exc_permissiondenied.value.status_code == status.HTTP_401_UNAUTHORIZED

    # Calling the decorator with no `exceptions` dict
    # still includes the `OperationalError` exception edge-case
    # for when `max_locks_per_transaction` is exceeded.
    @map_exceptions()
    def test_operationalerror_locks_exceeded():
        raise OperationalError(
            "HINT:  You might need to increase max_locks_per_transaction."
        )

    with pytest.raises(APIException) as exc_operationalerror:
        test_operationalerror_locks_exceeded()

    assert (
        exc_operationalerror.value.detail["error"]
        == "MAX_LOCKS_PER_TRANSACTION_EXCEEDED"
    )
    assert exc_operationalerror.value.detail["detail"] == (
        "The maximum number of PostgreSQL locks per transaction has been exhausted. "
        "Please increase `max_locks_per_transaction`."
    )
    assert exc_operationalerror.value.status_code == status.HTTP_400_BAD_REQUEST


def test_validate_body():
    factory = APIRequestFactory()

    request = Request(
        factory.post(
            "/some-page/",
            data=json.dumps({"field_1": "test"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(APIException) as api_exception_1:
        validate_body(TemporarySerializer)(func)(*[object, request])

    assert api_exception_1.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_1.value.detail["detail"]["field_2"][0]["error"] == (
        "This field is required."
    )
    assert api_exception_1.value.detail["detail"]["field_2"][0]["code"] == "required"
    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(
        factory.post(
            "/some-page/",
            data=json.dumps({"field_1": "test", "field_2": "wrong"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(APIException) as api_exception_2:
        validate_body(TemporarySerializer)(func)(*[object, request])

    assert api_exception_2.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_2.value.detail["detail"]["field_2"][0]["error"] == (
        '"wrong" is not a valid choice.'
    )
    assert api_exception_2.value.detail["detail"]["field_2"][0]["code"] == (
        "invalid_choice"
    )
    assert api_exception_2.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(
        factory.post(
            "/some-page/",
            data=json.dumps({"field_1": "test", "field_2": "choice_1"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    validate_body(TemporarySerializer)(func)(*[object, request])


def test_validate_query_parameter():
    factory = APIRequestFactory()

    request = Request(
        factory.post(
            "/some-page/?field_3=wrong_type",
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(QueryParameterValidationException) as api_exception_1:
        validate_query_parameters(TemporaryQueryParamSerializer)(func)(
            *[object, request]
        )

    assert api_exception_1.value.detail["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert api_exception_1.value.detail["detail"]["field_3"][0]["error"] == (
        "A valid integer is required."
    )
    assert api_exception_1.value.detail["detail"]["field_3"][0]["code"] == "invalid"
    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(
        factory.post(
            "/some-page/",
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(QueryParameterValidationException) as api_exception_2:
        validate_query_parameters(TemporaryQueryParamSerializer)(func)(
            *[object, request]
        )

    assert api_exception_2.value.detail["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert api_exception_2.value.detail["detail"]["field_3"][0]["error"] == (
        "This field is required."
    )
    assert api_exception_2.value.detail["detail"]["field_3"][0]["code"] == ("required")
    assert api_exception_2.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(
        factory.post(
            "/some-page/?field_3=5",
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    validate_query_parameters(TemporaryQueryParamSerializer)(func)(*[object, request])

    request = Request(
        factory.post(
            "/some-page/?field_3=-6",
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    validate_query_parameters(TemporaryQueryParamSerializer)(func)(*[object, request])

    # Make sure that having additional query parameters in the query string will not
    # have any effect on validating the parameters
    request = Request(
        factory.post(
            "/some-page/?field_3=-6&field_6=5",
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    validate_query_parameters(TemporaryQueryParamSerializer)(func)(*[object, request])


def test_validate_body_and_query_parameters():
    factory = APIRequestFactory()

    request = Request(
        factory.post(
            "/some-page/?field_3=wrong_type",
            data=json.dumps({"field_1": "test", "field_2": "choice_1"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(QueryParameterValidationException) as api_exception_1:
        validate_body(TemporarySerializer)(func)(*[object, request])
        validate_query_parameters(TemporaryQueryParamSerializer)(func)(
            *[object, request]
        )
    assert api_exception_1.value.detail["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"

    request = Request(
        factory.post(
            "/some-page/?field_3=5",
            data=json.dumps({"field_1": "test"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(RequestBodyValidationException) as api_exception_2:
        validate_body(TemporarySerializer)(func)(*[object, request])
        validate_query_parameters(TemporaryQueryParamSerializer)(func)(
            *[object, request]
        )
    assert api_exception_2.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    # When both the request body and the query parameters are incorrect
    # which Exception gets raised depends on the order of the decorators.
    request = Request(
        factory.post(
            "/some-page/?field_3=wrong_type",
            data=json.dumps({"field_1": "test"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(RequestBodyValidationException) as api_exception_3:
        validate_body(TemporarySerializer)(func)(*[object, request])
        validate_query_parameters(TemporaryQueryParamSerializer)(func)(
            *[object, request]
        )
    assert api_exception_3.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"

    request = Request(
        factory.post(
            "/some-page/?field_3=wrong_type",
            data=json.dumps({"field_1": "test"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(QueryParameterValidationException) as api_exception_4:
        validate_query_parameters(TemporaryQueryParamSerializer)(func)(
            *[object, request]
        )
        validate_body(TemporarySerializer)(func)(*[object, request])
    assert api_exception_4.value.detail["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"


def test_validate_body_custom_fields():
    factory = APIRequestFactory()
    registry = TemporaryTypeRegistry()
    registry.register(TemporaryInstanceType1())
    registry.register(TemporaryInstanceType2())

    request = Request(
        factory.post(
            "/some-page/",
            data=json.dumps({"missing": "type"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(APIException) as api_exception_1:
        validate_body_custom_fields(registry, "serializer_class")(func)(
            *[object, request]
        )

    assert api_exception_1.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_1.value.detail["detail"]["type"][0]["error"] == (
        "This field is required."
    )
    assert api_exception_1.value.detail["detail"]["type"][0]["code"] == "required"
    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(
        factory.post(
            "/some-page/",
            data=json.dumps({"type": "NOT_EXISTING"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(APIException) as api_exception_2:
        validate_body_custom_fields(registry)(func)(*[object, request])

    assert api_exception_2.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_2.value.detail["detail"]["type"][0]["error"] == (
        '"NOT_EXISTING" is not a valid choice.'
    )
    assert api_exception_2.value.detail["detail"]["type"][0]["code"] == "invalid_choice"
    assert api_exception_2.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(
        factory.post(
            "/some-page/",
            data=json.dumps({"type": "temporary_2"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(APIException) as api_exception_3:
        validate_body_custom_fields(registry)(func)(*[object, request])

    assert api_exception_3.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_3.value.detail["detail"]["name"][0]["error"] == (
        "This field is required."
    )
    assert api_exception_3.value.detail["detail"]["name"][0]["code"] == "required"
    assert api_exception_3.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(
        factory.post(
            "/some-page/",
            data=json.dumps({"type": "temporary_1"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(APIException) as api_exception_4:
        validate_body_custom_fields(
            registry, base_serializer_class=TemporaryBaseModelSerializer
        )(func)(*[object, request])

    assert api_exception_4.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_4.value.detail["detail"]["name"][0]["error"] == (
        "This field is required."
    )
    assert api_exception_4.value.detail["detail"]["name"][0]["code"] == "required"
    assert api_exception_4.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(
        factory.post(
            "/some-page/",
            data=json.dumps({"type": "temporary_2", "name": "test1"}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    with pytest.raises(APIException) as api_exception_5:
        validate_body_custom_fields(registry)(func)(*[object, request])

    assert api_exception_5.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_5.value.detail["detail"]["name"][0]["error"] == (
        "A valid integer is required."
    )
    assert api_exception_5.value.detail["detail"]["name"][0]["code"] == "invalid"
    assert api_exception_5.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(
        factory.post(
            "/some-page/",
            data=json.dumps({"type": "temporary_2", "name": 123}),
            content_type="application/json",
        ),
        parsers=[JSONParser()],
    )
    func = MagicMock()

    validate_body_custom_fields(registry)(func)(*[object, request])


def test_allowed_includes():
    factory = APIRequestFactory()

    request = Request(
        factory.get(
            "/some-page/",
            data={"include": "test_1,test_2"},
        )
    )

    @allowed_includes("test_1", "test_3")
    def test_1(self, request, test_1, test_3):
        assert test_1
        assert not test_3

    test_1(None, request)

    request = Request(
        factory.get(
            "/some-page/",
            data={"include": "test_3"},
        )
    )

    @allowed_includes("test_1", "test_3")
    def test_2(self, request, test_1, test_3):
        assert not test_1
        assert test_3

    test_2(None, request)

    request = Request(
        factory.get(
            "/some-page/",
        )
    )

    @allowed_includes("test_1", "test_3")
    def test_3(self, request, test_1, test_3):
        assert not test_1
        assert not test_3

    test_3(None, request)


def test_accept_timezone():
    factory = APIRequestFactory()

    request = Request(
        factory.get(
            "/some-page/",
            data={"timezone": "NOT_EXISTING"},
        )
    )

    @accept_timezone()
    def test_1(self, request, now):
        pass

    with pytest.raises(APIException) as api_exception:
        test_1(None, request)

    assert api_exception.value.detail["error"] == "UNKNOWN_TIME_ZONE_ERROR"

    request = Request(factory.get("/some-page/"))

    @accept_timezone()
    def test_1(self, request, now):
        assert now.tzinfo == timezone.utc

    test_1(None, request)

    request = Request(
        factory.get(
            "/some-page/",
            data={"timezone": "Etc/GMT+2"},
        )
    )

    @accept_timezone()
    def test_1(self, request, now):
        assert now.tzinfo == zoneinfo.ZoneInfo("Etc/GMT+2")

    test_1(None, request)


def test_request_data_types():
    class Fake:
        @require_request_data_type(dict)
        def callable(self, request, foo, bar):
            return list(request.data.keys())

    class fakerequest:
        def __init__(self, data):
            self.data = data

    with pytest.raises(RequestBodyValidationException):
        Fake().callable(fakerequest(""), None, None)

    assert Fake().callable(fakerequest({"a": 1}), None, None) == ["a"]
