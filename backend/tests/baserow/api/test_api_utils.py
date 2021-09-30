import pytest

from rest_framework import status, serializers
from rest_framework.exceptions import APIException
from rest_framework.serializers import CharField
from rest_framework.status import HTTP_404_NOT_FOUND
from baserow.api.exceptions import QueryParameterValidationException

from baserow.core.models import Group
from baserow.core.registry import (
    Instance,
    Registry,
    CustomFieldsInstanceMixin,
    ModelInstanceMixin,
)
from baserow.api.utils import (
    map_exceptions,
    validate_data,
    validate_data_custom_fields,
    get_serializer_class,
)


class TemporaryException(Exception):
    pass


class TemporaryException2(Exception):
    pass


class TemporarySerializer(serializers.Serializer):
    field_1 = serializers.CharField()
    field_2 = serializers.ChoiceField(choices=("choice_1", "choice_2"))


class TemporaryListSerializer(serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        kwargs["child"] = TemporarySerializer()
        super().__init__(*args, **kwargs)


class TemporarySerializerWithList(serializers.Serializer):
    field_3 = serializers.IntegerField()
    field_4 = serializers.ListField(child=serializers.IntegerField())


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


class TemporaryQueryParamSerializer(serializers.Serializer):
    field_5 = serializers.IntegerField(required=True)
    field_6 = serializers.CharField(max_length=20, required=False)


def test_map_exceptions():
    with pytest.raises(APIException) as api_exception_1:
        with map_exceptions({TemporaryException: "ERROR_TEMPORARY"}):
            raise TemporaryException

    assert api_exception_1.value.detail["error"] == "ERROR_TEMPORARY"
    assert api_exception_1.value.detail["detail"] == ""
    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST

    with pytest.raises(APIException) as api_exception_2:
        with map_exceptions(
            {
                TemporaryException: (
                    "ERROR_TEMPORARY_2",
                    HTTP_404_NOT_FOUND,
                    "Another message {e.message}",
                )
            }
        ):
            e = TemporaryException()
            e.message = "test"
            raise e

    assert api_exception_2.value.detail["error"] == "ERROR_TEMPORARY_2"
    assert api_exception_2.value.detail["detail"] == "Another message test"
    assert api_exception_2.value.status_code == status.HTTP_404_NOT_FOUND

    with pytest.raises(TemporaryException2):
        with map_exceptions({TemporaryException: "ERROR_TEMPORARY_3"}):
            raise TemporaryException2

    with map_exceptions({TemporaryException: "ERROR_TEMPORARY_4"}):
        pass


def test_validate_data():
    with pytest.raises(APIException) as api_exception_1:
        validate_data(TemporarySerializer, {"field_1": "test"})

    assert api_exception_1.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_1.value.detail["detail"]["field_2"][0]["error"] == (
        "This field is required."
    )
    assert api_exception_1.value.detail["detail"]["field_2"][0]["code"] == "required"
    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST

    with pytest.raises(APIException) as api_exception_2:
        validate_data(TemporarySerializer, {"field_1": "test", "field_2": "wrong"})

    assert api_exception_2.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_2.value.detail["detail"]["field_2"][0]["error"] == (
        '"wrong" is not a valid choice.'
    )
    assert api_exception_2.value.detail["detail"]["field_2"][0]["code"] == (
        "invalid_choice"
    )
    assert api_exception_2.value.status_code == status.HTTP_400_BAD_REQUEST

    validated_data = validate_data(
        TemporarySerializer, {"field_1": "test", "field_2": "choice_1"}
    )
    assert validated_data["field_1"] == "test"
    assert validated_data["field_2"] == "choice_1"
    assert len(validated_data.items()) == 2

    with pytest.raises(APIException) as api_exception_1:
        validate_data(
            TemporarySerializerWithList, {"field_3": "aaa", "field_4": ["a", "b"]}
        )

    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST
    assert api_exception_1.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_1.value.detail["detail"]["field_3"][0]["error"] == (
        "A valid integer is required."
    )
    assert api_exception_1.value.detail["detail"]["field_3"][0]["code"] == "invalid"

    assert len(api_exception_1.value.detail["detail"]["field_4"]) == 2
    assert api_exception_1.value.detail["detail"]["field_4"][0][0]["error"] == (
        "A valid integer is required."
    )
    assert api_exception_1.value.detail["detail"]["field_4"][0][0]["code"] == (
        "invalid"
    )
    assert api_exception_1.value.detail["detail"]["field_4"][1][0]["error"] == (
        "A valid integer is required."
    )
    assert api_exception_1.value.detail["detail"]["field_4"][1][0]["code"] == (
        "invalid"
    )

    with pytest.raises(APIException) as api_exception_3:
        validate_data(TemporaryListSerializer, [{"something": "nothing"}])

    assert api_exception_3.value.status_code == status.HTTP_400_BAD_REQUEST
    assert api_exception_3.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert len(api_exception_3.value.detail["detail"]) == 1
    assert api_exception_3.value.detail["detail"][0]["field_1"][0]["code"] == "required"
    assert api_exception_3.value.detail["detail"][0]["field_2"][0]["code"] == "required"

    with pytest.raises(QueryParameterValidationException) as api_exception_4:
        validate_data(
            TemporaryQueryParamSerializer,
            {"field_5": "wrong_type"},
            exception_to_raise=QueryParameterValidationException,
        )
    assert api_exception_4.value.status_code == status.HTTP_400_BAD_REQUEST
    assert api_exception_4.value.detail["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert api_exception_4.value.detail["detail"]["field_5"][0]["code"] == "invalid"
    assert api_exception_4.value.detail["detail"]["field_5"][0]["error"] == (
        "A valid integer is required."
    )

    with pytest.raises(QueryParameterValidationException) as api_exception_5:
        validate_data(
            TemporaryQueryParamSerializer,
            {},
            exception_to_raise=QueryParameterValidationException,
        )
    assert api_exception_5.value.status_code == status.HTTP_400_BAD_REQUEST
    assert api_exception_5.value.detail["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert api_exception_5.value.detail["detail"]["field_5"][0]["code"] == "required"
    assert api_exception_5.value.detail["detail"]["field_5"][0]["error"] == (
        "This field is required."
    )

    with pytest.raises(QueryParameterValidationException) as api_exception_6:
        validate_data(
            TemporaryQueryParamSerializer,
            {"field_5": 5, "field_6": "string_is_way_too_long"},
            exception_to_raise=QueryParameterValidationException,
        )
    assert api_exception_6.value.status_code == status.HTTP_400_BAD_REQUEST
    assert api_exception_6.value.detail["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert api_exception_6.value.detail["detail"]["field_6"][0]["code"] == "max_length"
    assert api_exception_6.value.detail["detail"]["field_6"][0]["error"] == (
        "Ensure this field has no more than 20 characters."
    )

    with pytest.raises(QueryParameterValidationException) as api_exception_7:
        validate_data(
            TemporaryQueryParamSerializer,
            {"field_5": "wrong_type", "field_6": "string_is_way_too_long"},
            exception_to_raise=QueryParameterValidationException,
        )
    assert api_exception_7.value.status_code == status.HTTP_400_BAD_REQUEST
    assert api_exception_7.value.detail["error"] == "ERROR_QUERY_PARAMETER_VALIDATION"
    assert api_exception_7.value.detail["detail"]["field_6"][0]["code"] == "max_length"
    assert api_exception_7.value.detail["detail"]["field_6"][0]["error"] == (
        "Ensure this field has no more than 20 characters."
    )
    assert api_exception_7.value.detail["detail"]["field_5"][0]["code"] == "invalid"
    assert api_exception_7.value.detail["detail"]["field_5"][0]["error"] == (
        "A valid integer is required."
    )


def test_validate_data_custom_fields():
    registry = TemporaryTypeRegistry()
    registry.register(TemporaryInstanceType1())
    registry.register(TemporaryInstanceType2())

    with pytest.raises(APIException) as api_exception:
        validate_data_custom_fields("NOT_EXISTING", registry, {})

    assert api_exception.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception.value.detail["detail"]["type"][0]["error"] == (
        '"NOT_EXISTING" is not a valid choice.'
    )
    assert api_exception.value.detail["detail"]["type"][0]["code"] == "invalid_choice"
    assert api_exception.value.status_code == status.HTTP_400_BAD_REQUEST

    with pytest.raises(APIException) as api_exception_2:
        validate_data_custom_fields("temporary_2", registry, {})

    assert api_exception_2.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_2.value.detail["detail"]["name"][0]["error"] == (
        "This field is required."
    )
    assert api_exception_2.value.detail["detail"]["name"][0]["code"] == "required"
    assert api_exception_2.value.status_code == status.HTTP_400_BAD_REQUEST

    with pytest.raises(APIException) as api_exception_3:
        validate_data_custom_fields("temporary_2", registry, {"name": "test1"})

    assert api_exception_3.value.detail["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert api_exception_3.value.detail["detail"]["name"][0]["error"] == (
        "A valid integer is required."
    )
    assert api_exception_3.value.detail["detail"]["name"][0]["code"] == "invalid"
    assert api_exception_3.value.status_code == status.HTTP_400_BAD_REQUEST

    data = validate_data_custom_fields("temporary_2", registry, {"name": 123})
    assert data["name"] == 123


@pytest.mark.django_db
def test_get_serializer_class(data_fixture):
    group = data_fixture.create_group(name="Group 1")

    group_serializer = get_serializer_class(Group, ["name"])(group)
    assert group_serializer.data == {"name": "Group 1"}
    assert group_serializer.__class__.__name__ == "GroupSerializer"

    group_serializer_2 = get_serializer_class(
        Group, ["id", "name"], {"id": CharField()}
    )(group)
    assert group_serializer_2.data == {"id": str(group.id), "name": "Group 1"}
