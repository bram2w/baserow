import pytest
import json

from unittest.mock import MagicMock

from django.http.request import HttpRequest

from rest_framework import status, serializers
from rest_framework.request import Request
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import APIException
from rest_framework.test import APIRequestFactory

from baserow.api.v0.decorators import map_exceptions, validate_body


class TemporaryException(Exception):
    pass


class TemporarySerializer(serializers.Serializer):
    field_1 = serializers.CharField()
    field_2 = serializers.ChoiceField(choices=('choice_1', 'choice_2'))


def test_map_exceptions():
    @map_exceptions({
        TemporaryException: 'ERROR_TEMPORARY'
    })
    def test_1():
        raise TemporaryException

    with pytest.raises(APIException) as api_exception_1:
        test_1()

    assert api_exception_1.value.detail['error'] == 'ERROR_TEMPORARY'
    assert api_exception_1.value.detail['detail'] == ''
    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST

    @map_exceptions({
        TemporaryException: ('ERROR_TEMPORARY_2', 404, 'Another message')
    })
    def test_2():
        raise TemporaryException

    with pytest.raises(APIException) as api_exception_2:
        test_2()

    assert api_exception_2.value.detail['error'] == 'ERROR_TEMPORARY_2'
    assert api_exception_2.value.detail['detail'] == 'Another message'
    assert api_exception_2.value.status_code == status.HTTP_404_NOT_FOUND

    @map_exceptions({
        TemporaryException: 'ERROR_TEMPORARY_3'
    })
    def test_3():
        pass

    test_3()


def test_validate_body():
    factory = APIRequestFactory()

    request = Request(factory.post(
        '/some-page/',
        data=json.dumps({'field_1': 'test'}),
        content_type='application/json'
    ), parsers=[JSONParser()])
    func = MagicMock()

    with pytest.raises(APIException) as api_exception_1:
        validate_body(TemporarySerializer)(func)(*[object, request])

    assert api_exception_1.value.detail['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert api_exception_1.value.detail['detail']['field_2'][0]['error'] == \
           'This field is required.'
    assert api_exception_1.value.detail['detail']['field_2'][0]['code'] == 'required'
    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(factory.post(
        '/some-page/',
        data=json.dumps({'field_1': 'test', 'field_2': 'wrong'}),
        content_type='application/json'
    ), parsers=[JSONParser()])
    func = MagicMock()

    with pytest.raises(APIException) as api_exception_1:
        validate_body(TemporarySerializer)(func)(*[object, request])

    assert api_exception_1.value.detail['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert api_exception_1.value.detail['detail']['field_2'][0]['error'] == \
        '"wrong" is not a valid choice.'
    assert api_exception_1.value.detail['detail']['field_2'][0]['code'] == \
        'invalid_choice'
    assert api_exception_1.value.status_code == status.HTTP_400_BAD_REQUEST

    request = Request(factory.post(
        '/some-page/',
        data=json.dumps({'field_1': 'test', 'field_2': 'choice_1'}),
        content_type='application/json'
    ), parsers=[JSONParser()])
    func = MagicMock()

    validate_body(TemporarySerializer)(func)(*[object, request])

