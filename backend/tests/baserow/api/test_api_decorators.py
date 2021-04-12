import pytest
import json

from unittest.mock import MagicMock

from rest_framework.status import HTTP_404_NOT_FOUND

from rest_framework import status, serializers
from rest_framework.request import Request
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import APIException
from rest_framework.test import APIRequestFactory

from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_body_custom_fields,
    allowed_includes,
)
from baserow.core.models import Group
from baserow.core.registry import (
    Instance,
    Registry,
    CustomFieldsInstanceMixin,
    ModelInstanceMixin,
)


class TemporaryException(Exception):
    pass


class TemporarySerializer(serializers.Serializer):
    field_1 = serializers.CharField()
    field_2 = serializers.ChoiceField(choices=("choice_1", "choice_2"))


class TemporaryBaseModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("name",)


class TemporaryInstance(CustomFieldsInstanceMixin, ModelInstanceMixin, Instance):
    pass


class TemporaryInstanceType1(TemporaryInstance):
    type = "temporary_1"
    model_class = Group


class TemporaryInstanceType2(TemporaryInstance):
    type = "temporary_2"
    model_class = Group
    serializer_field_names = ["name"]
    serializer_field_overrides = {"name": serializers.IntegerField()}


class TemporaryTypeRegistry(Registry):
    name = "temporary"


def test_map_exceptions():
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
