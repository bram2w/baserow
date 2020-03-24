import pytest

from django.shortcuts import reverse


@pytest.mark.django_db
def test_list_views(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table, order=0, name='Color',
                                                text_default='white')
    number_field = data_fixture.create_number_field(table=table, order=1,
                                                    name='Horsepower')
    boolean_field = data_fixture.create_boolean_field(table=table, order=2,
                                                      name='For sale')
    grid = data_fixture.create_grid_view(table=table)
    grid_2 = data_fixture.create_grid_view()

    model = grid.table.get_model()
    row_1 = model.objects.create(**{
        f'field_{text_field.id}': 'Green',
        f'field_{number_field.id}': 10,
        f'field_{boolean_field.id}': False
    })
    row_2 = model.objects.create()
    row_3 = model.objects.create(**{
        f'field_{text_field.id}': 'Orange',
        f'field_{number_field.id}': 100,
        f'field_{boolean_field.id}': True
    })
    row_4 = model.objects.create(**{
        f'field_{text_field.id}': 'Purple',
        f'field_{number_field.id}': 1000,
        f'field_{boolean_field.id}': False
    })

    url = reverse('api_v0:database:views:grid:list', kwargs={'view_id': 999})
    response = api_client.get(
        url,
        **{'HTTP_AUTHORIZATION': f'JWT {token}'}
    )
    assert response.status_code == 404
    assert response.json()['error'] == 'ERROR_GRID_DOES_NOT_EXIST'

    url = reverse('api_v0:database:views:grid:list', kwargs={'view_id': grid_2.id})
    response = api_client.get(
        url,
        **{'HTTP_AUTHORIZATION': f'JWT {token}'}
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:views:grid:list', kwargs={'view_id': grid.id})
    response = api_client.get(
        url,
        **{'HTTP_AUTHORIZATION': f'JWT {token}'}
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['count'] == 4
    assert not response_json['previous']
    assert not response_json['next']
    assert len(response_json['results']) == 4
    assert response_json['results'][0]['id'] == row_1.id
    assert response_json['results'][0][f'field_{text_field.id}'] == 'Green'
    assert response_json['results'][0][f'field_{number_field.id}'] == 10
    assert not response_json['results'][0][f'field_{boolean_field.id}']
    assert response_json['results'][1]['id'] == row_2.id
    assert response_json['results'][2]['id'] == row_3.id
    assert response_json['results'][3]['id'] == row_4.id

    url = reverse('api_v0:database:views:grid:list', kwargs={'view_id': grid.id})
    response = api_client.get(
        url,
        {'size': 2},
        **{'HTTP_AUTHORIZATION': f'JWT {token}'}
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['count'] == 4
    assert not response_json['previous']
    assert response_json['next']
    assert len(response_json['results']) == 2
    assert response_json['results'][0]['id'] == row_1.id
    assert response_json['results'][1]['id'] == row_2.id

    url = reverse('api_v0:database:views:grid:list', kwargs={'view_id': grid.id})
    response = api_client.get(
        url,
        {'size': 2, 'page': 2},
        **{'HTTP_AUTHORIZATION': f'JWT {token}'}
    )
    response_json = response.json()
    assert response_json['count'] == 4
    assert response_json['previous']
    assert not response_json['next']
    assert len(response_json['results']) == 2
    assert response_json['results'][0]['id'] == row_3.id
    assert response_json['results'][1]['id'] == row_4.id

    url = reverse('api_v0:database:views:grid:list', kwargs={'view_id': grid.id})
    response = api_client.get(
        url,
        {'size': 2, 'page': 999},
        **{'HTTP_AUTHORIZATION': f'JWT {token}'}
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'ERROR_INVALID_PAGE'

    url = reverse('api_v0:database:views:grid:list', kwargs={'view_id': grid.id})
    response = api_client.get(
        url,
        {'limit': 2},
        **{'HTTP_AUTHORIZATION': f'JWT {token}'}
    )
    response_json = response.json()
    assert response_json['count'] == 4
    assert response_json['results'][0]['id'] == row_1.id
    assert response_json['results'][1]['id'] == row_2.id

    url = reverse('api_v0:database:views:grid:list', kwargs={'view_id': grid.id})
    response = api_client.get(
        url,
        {'limit': 1, 'offset': 2},
        **{'HTTP_AUTHORIZATION': f'JWT {token}'}
    )
    response_json = response.json()
    assert response_json['count'] == 4
    assert response_json['results'][0]['id'] == row_3.id

    row_1.delete()
    row_2.delete()
    row_3.delete()
    row_4.delete()

    url = reverse('api_v0:database:views:grid:list', kwargs={'view_id': grid.id})
    response = api_client.get(
        url,
        **{'HTTP_AUTHORIZATION': f'JWT {token}'}
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json['count'] == 0
    assert not response_json['previous']
    assert not response_json['next']
    assert len(response_json['results']) == 0
