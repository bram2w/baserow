import pytest

from django.contrib.auth import get_user_model
from django.shortcuts import reverse


User = get_user_model()


@pytest.mark.django_db
def test_create_user(client):
    response = client.post(reverse('api_v0:user:index'), {
        'name': 'Test1',
        'email': 'test@test.nl',
        'password': 'test12'
    }, format='json')

    assert response.status_code == 200
    user = User.objects.get(email='test@test.nl')
    assert user.first_name == 'Test1'
    assert user.email == 'test@test.nl'
    assert user.password != ''

    response_failed = client.post(reverse('api_v0:user:index'), {
        'name': 'Test1',
        'email': 'test@test.nl',
        'password': 'test12'
    }, format='json')

    assert response_failed.status_code == 400
    assert response_failed.json()['error'] == 'ERROR_ALREADY_EXISTS'

    response_failed_2 = client.post(reverse('api_v0:user:index'), {
        'email': 'test'
    }, format='json')

    assert response_failed_2.status_code == 400
