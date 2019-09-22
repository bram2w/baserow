import pytest

from django.shortcuts import reverse

from baserow.contrib.database.models import Database


@pytest.mark.django_db
def test_list_applications(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    group_1 = data_fixture.create_group(user=user)
    group_2 = data_fixture.create_group()
    application_1 = data_fixture.create_database_application(group=group_1, order=1)
    application_2 = data_fixture.create_database_application(group=group_1, order=3)
    application_3 = data_fixture.create_database_application(group=group_1, order=2)
    data_fixture.create_database_application(group=group_2, order=1)

    response = api_client.get(
        reverse('api_v0:applications:list', kwargs={'group_id': group_1.id}), **{
            'HTTP_AUTHORIZATION': f'JWT {token}'
        }
    )
    assert response.status_code == 200
    response_json = response.json()

    assert len(response_json) == 3

    assert response_json[0]['id'] == application_1.id
    assert response_json[0]['type'] == 'database'

    assert response_json[1]['id'] == application_3.id
    assert response_json[1]['type'] == 'database'

    assert response_json[2]['id'] == application_2.id
    assert response_json[2]['type'] == 'database'

    response = api_client.get(
        reverse('api_v0:applications:list', kwargs={'group_id': group_2.id}), **{
            'HTTP_AUTHORIZATION': f'JWT {token}'
        }
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_create_application(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    group_2 = data_fixture.create_group(user=user_2)

    response = api_client.post(
        reverse('api_v0:applications:list', kwargs={'group_id': group.id}),
        {
            'name': 'Test 1',
            'type': 'NOT_EXISTING'
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert response_json['detail']['type'][0]['code'] == 'invalid_choice'

    response = api_client.post(
        reverse('api_v0:applications:list', kwargs={'group_id': group_2.id}),
        {
            'name': 'Test 1',
            'type': 'database'
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404

    response = api_client.post(
        reverse('api_v0:applications:list', kwargs={'group_id': group.id}),
        {
            'name': 'Test 1',
            'type': 'database'
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['type'] == 'database'

    database = Database.objects.filter()[0]
    assert response_json['id'] == database.id
    assert response_json['name'] == database.name
    assert response_json['order'] == database.order


@pytest.mark.django_db
def test_update_application(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    group_2 = data_fixture.create_group(user=user_2)
    application = data_fixture.create_database_application(group=group)
    application_2 = data_fixture.create_database_application(group=group_2)

    url = reverse('api_v0:applications:item',
                  kwargs={'application_id': application_2.id})
    response = api_client.patch(
        url,
        {'name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:applications:item', kwargs={'application_id': application.id})
    response = api_client.patch(
        url,
        {'UNKNOWN_FIELD': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_REQUEST_BODY_VALIDATION'

    url = reverse('api_v0:applications:item', kwargs={'application_id': application.id})
    response = api_client.patch(
        url,
        {'name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['id'] == application.id
    assert response_json['name'] == 'Test 1'

    application.refresh_from_db()
    assert application.name == 'Test 1'


@pytest.mark.django_db
def test_delete_application(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    group_2 = data_fixture.create_group(user=user_2)
    application = data_fixture.create_database_application(group=group)
    application_2 = data_fixture.create_database_application(group=group_2)

    url = reverse('api_v0:applications:item',
                  kwargs={'application_id': application_2.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:applications:item', kwargs={'application_id': application.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 204

    assert Database.objects.all().count() == 1
