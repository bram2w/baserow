import pytest

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from django.shortcuts import reverse

from baserow.contrib.database.views.models import GridView


@pytest.mark.django_db
def test_list_views(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    table_1 = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    view_1 = data_fixture.create_grid_view(table=table_1, order=1)
    view_2 = data_fixture.create_grid_view(table=table_1, order=3)
    view_3 = data_fixture.create_grid_view(table=table_1, order=2)
    data_fixture.create_grid_view(table=table_2, order=1)

    response = api_client.get(
        reverse('api:database:views:list', kwargs={'table_id': table_1.id}), **{
            'HTTP_AUTHORIZATION': f'JWT {token}'
        }
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert len(response_json) == 3

    assert response_json[0]['id'] == view_1.id
    assert response_json[0]['type'] == 'grid'

    assert response_json[1]['id'] == view_3.id
    assert response_json[1]['type'] == 'grid'

    assert response_json[2]['id'] == view_2.id
    assert response_json[2]['type'] == 'grid'

    response = api_client.get(
        reverse('api:database:views:list', kwargs={'table_id': table_2.id}), **{
            'HTTP_AUTHORIZATION': f'JWT {token}'
        }
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    response = api_client.get(
        reverse('api:database:views:list', kwargs={'table_id': 999999}), **{
            'HTTP_AUTHORIZATION': f'JWT {token}'
        }
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()['error'] == 'ERROR_TABLE_DOES_NOT_EXIST'


@pytest.mark.django_db
def test_create_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()

    response = api_client.post(
        reverse('api:database:views:list', kwargs={'table_id': table.id}),
        {
            'name': 'Test 1',
            'type': 'NOT_EXISTING'
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert response_json['detail']['type'][0]['code'] == 'invalid_choice'

    response = api_client.post(
        reverse('api:database:views:list', kwargs={'table_id': 99999}),
        {'name': 'Test 1', 'type': 'grid'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()['error'] == 'ERROR_TABLE_DOES_NOT_EXIST'

    response = api_client.post(
        reverse('api:database:views:list', kwargs={'table_id': table_2.id}),
        {'name': 'Test 1', 'type': 'grid'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    response = api_client.post(
        reverse('api:database:views:list', kwargs={'table_id': table.id}),
        {
            'name': 'Test 1',
            'type': 'grid'
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json['type'] == 'grid'

    grid = GridView.objects.filter()[0]
    assert response_json['id'] == grid.id
    assert response_json['name'] == grid.name
    assert response_json['order'] == grid.order


@pytest.mark.django_db
def test_get_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user_2)
    view = data_fixture.create_grid_view(table=table)
    view_2 = data_fixture.create_grid_view(table=table_2)

    url = reverse('api:database:views:item', kwargs={'view_id': view_2.id})
    response = api_client.get(
        url,
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api:database:views:item', kwargs={'view_id': 99999})
    response = api_client.get(
        url,
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_404_NOT_FOUND

    url = reverse('api:database:views:item', kwargs={'view_id': view.id})
    response = api_client.get(
        url,
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json['id'] == view.id
    assert response_json['type'] == 'grid'
    assert response_json['table']['id'] == table.id


@pytest.mark.django_db
def test_update_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user_2)
    view = data_fixture.create_grid_view(table=table)
    view_2 = data_fixture.create_grid_view(table=table_2)

    url = reverse('api:database:views:item', kwargs={'view_id': view_2.id})
    response = api_client.patch(
        url,
        {'name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api:database:views:item', kwargs={'view_id': 999999})
    response = api_client.patch(
        url,
        {'name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()['error'] == 'ERROR_VIEW_DOES_NOT_EXIST'

    url = reverse('api:database:views:item', kwargs={'view_id': view.id})
    response = api_client.patch(
        url,
        {'UNKNOWN_FIELD': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_200_OK

    url = reverse('api:database:views:item', kwargs={'view_id': view.id})
    response = api_client.patch(
        url,
        {'name': 'Test 1'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json['id'] == view.id
    assert response_json['name'] == 'Test 1'

    view.refresh_from_db()
    assert view.name == 'Test 1'


@pytest.mark.django_db
def test_delete_view(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user_2)
    view = data_fixture.create_grid_view(table=table)
    view_2 = data_fixture.create_grid_view(table=table_2)

    url = reverse('api:database:views:item', kwargs={'view_id': view_2.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api:database:views:item', kwargs={'view_id': 99999})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()['error'] == 'ERROR_VIEW_DOES_NOT_EXIST'

    url = reverse('api:database:views:item', kwargs={'view_id': view.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 204

    assert GridView.objects.all().count() == 1
