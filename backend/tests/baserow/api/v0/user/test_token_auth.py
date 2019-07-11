import pytest
from unittest.mock import patch
from datetime import datetime

from django.shortcuts import reverse
from django.contrib.auth import get_user_model

from rest_framework_jwt.settings import api_settings


jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


User = get_user_model()


@pytest.mark.django_db
def test_token_auth(client, data_fixture):
    data_fixture.create_user(email='test@test.nl', password='password',
                             first_name='Test1')

    response = client.post(reverse('api:user:token_auth'), {
        'username': 'no_existing@test.nl',
        'password': 'password'
    })
    json = response.json()

    assert response.status_code == 400
    assert len(json['non_field_errors']) > 0

    response = client.post(reverse('api:user:token_auth'), {
        'username': 'test@test.nl',
        'password': 'wrong_password'
    })
    json = response.json()

    assert response.status_code == 400
    assert len(json['non_field_errors']) > 0

    response = client.post(reverse('api:user:token_auth'), {
        'username': 'test@test.nl',
        'password': 'password'
    })
    json = response.json()

    assert response.status_code == 200
    assert 'token' in json
    assert 'user' in json
    assert json['user']['username'] == 'test@test.nl'
    assert json['user']['first_name'] == 'Test1'


@pytest.mark.django_db
def test_token_refresh(client, data_fixture):
    user = data_fixture.create_user(email='test@test.nl', password='password',
                                    first_name='Test1')

    response = client.post(reverse('api:user:token_refresh'), {'token': 'WRONG_TOKEN'})
    assert response.status_code == 400

    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)

    response = client.post(reverse('api:user:token_refresh'), {'token': token})
    assert response.status_code == 200
    assert 'token' in response.json()

    with patch('rest_framework_jwt.utils.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2019, 1, 1, 1, 1, 1, 0)
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        response = client.post(reverse('api:user:token_refresh'), {'token': token})
        assert response.status_code == 400
