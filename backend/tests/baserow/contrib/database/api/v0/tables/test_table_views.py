import pytest

from django.shortcuts import reverse

from baserow.contrib.database.table.models import Table


@pytest.mark.django_db
def test_list_tables(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    database_2 = data_fixture.create_database_application()
    table_1 = data_fixture.create_database_table(database=database, order=2)
    table_2 = data_fixture.create_database_table(database=database, order=1)
    table_3 = data_fixture.create_database_table(database=database_2)

    url = reverse('api_v0:database:tables:list', kwargs={'database_id': database.id})
    response = api_client.get(url, HTTP_AUTHORIZATION=f'JWT {token}')
    response_json = response.json()
    assert response.status_code == 200
    assert len(response_json) == 2
    assert response_json[0]['id'] == table_2.id
    assert response_json[1]['id'] == table_1.id

    url = reverse('api_v0:database:tables:list', kwargs={'database_id': database_2.id})
    response = api_client.get(url, HTTP_AUTHORIZATION=f'JWT {token}')
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:tables:list', kwargs={'database_id': 9999})
    response = api_client.get(url, **{
        'HTTP_AUTHORIZATION': f'JWT {token}'
    })
    assert response.status_code == 404


@pytest.mark.django_db
def test_create_table(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    database_2 = data_fixture.create_database_application()

    url = reverse('api_v0:database:tables:list', kwargs={'database_id': database.id})
    response = api_client.post(
        url,
        {'name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 200
    json_response = response.json()

    Table.objects.all().count() == 1
    table = Table.objects.filter(database=database).first()

    assert table.order == json_response['order'] == 1
    assert table.name == json_response['name']
    assert table.id == json_response['id']

    url = reverse('api_v0:database:tables:list', kwargs={'database_id': database_2.id})
    response = api_client.post(
        url,
        {'name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:tables:list', kwargs={'database_id': database.id})
    response = api_client.post(
        url,
        {'not_a_name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'ERROR_REQUEST_BODY_VALIDATION'

    url = reverse('api_v0:database:tables:list', kwargs={'database_id': 9999})
    response = api_client.post(
        url,
        {'name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_get_table(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()

    url = reverse('api_v0:database:tables:item', kwargs={'table_id': table_1.id})
    response = api_client.get(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['id'] == table_1.id
    assert json_response['name'] == table_1.name
    assert json_response['order'] == table_1.order

    url = reverse('api_v0:database:tables:item', kwargs={'table_id': table_2.id})
    response = api_client.get(url, HTTP_AUTHORIZATION=f'JWT {token}')
    json_response = response.json()
    assert response.status_code == 400
    assert json_response['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:tables:item', kwargs={'table_id': 9999})
    response = api_client.get(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_table(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()

    url = reverse('api_v0:database:tables:item', kwargs={'table_id': table_1.id})
    response = api_client.patch(
        url,
        {'name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 200
    response_json = response.json()

    table_1.refresh_from_db()

    assert response_json['id'] == table_1.id
    assert response_json['name'] == table_1.name == 'New name'

    url = reverse('api_v0:database:tables:item', kwargs={'table_id': table_2.id})
    response = api_client.patch(
        url,
        {'name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:tables:item', kwargs={'table_id': table_1.id})
    response = api_client.patch(
        url,
        {'not_a_name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_REQUEST_BODY_VALIDATION'

    url = reverse('api_v0:database:tables:item', kwargs={'table_id': 999})
    response = api_client.patch(
        url,
        {'name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_table(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()

    assert Table.objects.all().count() == 2
    url = reverse('api_v0:database:tables:item', kwargs={'table_id': table_1.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 204
    assert Table.objects.all().count() == 1

    url = reverse('api_v0:database:tables:item', kwargs={'table_id': table_2.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:tables:item', kwargs={'table_id': 9999})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 404


@pytest.mark.django_db
def test_get_database_application_with_tables(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    database = data_fixture.create_database_application(user=user)
    table_1 = data_fixture.create_database_table(database=database, order=0)
    table_2 = data_fixture.create_database_table(database=database, order=1)
    table_3 = data_fixture.create_database_table()

    url = reverse('api_v0:applications:item', kwargs={'application_id': database.id})
    response = api_client.get(
        url,
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 200
    assert len(response_json['tables']) == 2
    assert response_json['tables'][0]['id'] == table_1.id
    assert response_json['tables'][1]['id'] == table_2.id
