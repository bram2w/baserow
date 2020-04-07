from decimal import Decimal

import pytest

from django.shortcuts import reverse


@pytest.mark.django_db
def test_create_row(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    text_field = data_fixture.create_text_field(table=table, order=0, name='Color',
                                                text_default='white')
    number_field = data_fixture.create_number_field(table=table, order=1,
                                                    name='Horsepower')
    boolean_field = data_fixture.create_boolean_field(table=table, order=2,
                                                      name='For sale')
    text_field_2 = data_fixture.create_text_field(table=table, order=3,
                                                  name='Description')

    response = api_client.post(
        reverse('api_v0:database:rows:list', kwargs={'table_id': 99999}),
        {'name': 'Test 1', 'type': 'text'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404

    response = api_client.post(
        reverse('api_v0:database:rows:list', kwargs={'table_id': table_2.id}),
        {f'field_{text_field.id}': 'Green'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    response = api_client.post(
        reverse('api_v0:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{text_field.id}': 'Green',
            f'field_{number_field.id}': -10,
            f'field_{boolean_field.id}': None,
            f'field_{text_field_2.id}': None
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert len(response_json['detail']) == 2
    assert response_json['detail'][f'field_{number_field.id}'][0]['code'] == 'min_value'
    assert response_json['detail'][f'field_{boolean_field.id}'][0]['code'] == 'null'

    response = api_client.post(
        reverse('api_v0:database:rows:list', kwargs={'table_id': table.id}),
        {},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json_row_1 = response.json()
    assert response.status_code == 200
    assert response_json_row_1[f'field_{text_field.id}'] == 'white'
    assert not response_json_row_1[f'field_{number_field.id}']
    assert response_json_row_1[f'field_{boolean_field.id}'] == False
    assert response_json_row_1[f'field_{text_field_2.id}'] == None

    response = api_client.post(
        reverse('api_v0:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{number_field.id}': None,
            f'field_{boolean_field.id}': False,
            f'field_{text_field_2.id}': '',
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json_row_2 = response.json()
    assert response.status_code == 200
    assert response_json_row_2[f'field_{text_field.id}'] == 'white'
    assert not response_json_row_2[f'field_{number_field.id}']
    assert response_json_row_2[f'field_{boolean_field.id}'] == False
    assert response_json_row_2[f'field_{text_field_2.id}'] == ''

    response = api_client.post(
        reverse('api_v0:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{text_field.id}': 'Green',
            f'field_{number_field.id}': 120,
            f'field_{boolean_field.id}': True,
            f'field_{text_field_2.id}': 'Not important',
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json_row_3 = response.json()
    assert response.status_code == 200
    assert response_json_row_3[f'field_{text_field.id}'] == 'Green'
    assert response_json_row_3[f'field_{number_field.id}'] == 120
    assert response_json_row_3[f'field_{boolean_field.id}']
    assert response_json_row_3[f'field_{text_field_2.id}'] == 'Not important'

    model = table.get_model()
    assert model.objects.all().count() == 3
    rows = model.objects.all().order_by('id')

    row_1 = rows[0]
    assert row_1.id == response_json_row_1['id']
    assert getattr(row_1, f'field_{text_field.id}') == 'white'
    assert getattr(row_1, f'field_{number_field.id}') == None
    assert getattr(row_1, f'field_{boolean_field.id}') == False
    assert getattr(row_1, f'field_{text_field_2.id}') == None

    row_2 = rows[1]
    assert row_2.id == response_json_row_2['id']
    assert getattr(row_2, f'field_{text_field.id}') == 'white'
    assert getattr(row_2, f'field_{number_field.id}') == None
    assert getattr(row_2, f'field_{boolean_field.id}') == False
    assert getattr(row_1, f'field_{text_field_2.id}') == None

    row_3 = rows[2]
    assert row_3.id == response_json_row_3['id']
    assert getattr(row_3, f'field_{text_field.id}') == 'Green'
    assert getattr(row_3, f'field_{number_field.id}') == 120
    assert getattr(row_3, f'field_{boolean_field.id}') == True
    assert getattr(row_3, f'field_{text_field_2.id}') == 'Not important'


@pytest.mark.django_db
def test_update_row(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    text_field = data_fixture.create_text_field(table=table, order=0, name='Color',
                                                text_default='white')
    number_field = data_fixture.create_number_field(table=table, order=1,
                                                    name='Horsepower')
    boolean_field = data_fixture.create_boolean_field(table=table, order=2,
                                                      name='For sale')

    model = table.get_model()
    row_1 = model.objects.create()
    row_2 = model.objects.create()

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': 9999,
        'row_id': 9999
    })
    response = api_client.patch(
        url,
        {f'field_{text_field.id}': 'Orange'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404
    assert response.json()['error'] == 'ERROR_TABLE_DOES_NOT_EXIST'

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table_2.id,
        'row_id': row_1.id
    })
    response = api_client.patch(
        url,
        {f'field_{text_field.id}': 'Orange'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 400
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table.id,
        'row_id': 99999
    })
    response = api_client.patch(
        url,
        {f'field_{text_field.id}': 'Orange'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404
    assert response.json()['error'] == 'ERROR_ROW_DOES_NOT_EXIST'

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table.id,
        'row_id': row_1.id
    })
    response = api_client.patch(
        url,
        {
            f'field_{text_field.id}': 'Green',
            f'field_{number_field.id}': -10,
            f'field_{boolean_field.id}': None
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 400
    assert response_json['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert len(response_json['detail']) == 2
    assert response_json['detail'][f'field_{number_field.id}'][0]['code'] == 'min_value'
    assert response_json['detail'][f'field_{boolean_field.id}'][0]['code'] == 'null'

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table.id,
        'row_id': row_1.id
    })
    response = api_client.patch(
        url,
        {
            f'field_{text_field.id}': 'Green',
            f'field_{number_field.id}': 120,
            f'field_{boolean_field.id}': True
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json_row_1 = response.json()
    assert response.status_code == 200
    assert response_json_row_1['id'] == row_1.id
    assert response_json_row_1[f'field_{text_field.id}'] == 'Green'
    assert response_json_row_1[f'field_{number_field.id}'] == 120
    assert response_json_row_1[f'field_{boolean_field.id}'] == True

    row_1.refresh_from_db()
    assert getattr(row_1, f'field_{text_field.id}') == 'Green'
    assert getattr(row_1, f'field_{number_field.id}') == 120
    assert getattr(row_1, f'field_{boolean_field.id}') == True

    response = api_client.patch(
        url,
        {f'field_{text_field.id}': 'Orange'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json_row_1 = response.json()
    assert response.status_code == 200
    assert response_json_row_1[f'field_{text_field.id}'] == 'Orange'
    # Because the model is generated only for the field we want to change the other
    # fields are not included in the serializer.
    assert f'field_{number_field.id}' not in response_json_row_1
    assert f'field_{boolean_field.id}' not in response_json_row_1

    row_1.refresh_from_db()
    assert getattr(row_1, f'field_{text_field.id}') == 'Orange'
    assert getattr(row_1, f'field_{number_field.id}') == 120
    assert getattr(row_1, f'field_{boolean_field.id}') == True

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table.id,
        'row_id': row_2.id
    })
    response = api_client.patch(
        url,
        {
            f'field_{text_field.id}': 'Blue',
            f'field_{number_field.id}': 50,
            f'field_{boolean_field.id}': False
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json_row_2 = response.json()
    assert response.status_code == 200
    assert response_json_row_2['id'] == row_2.id
    assert response_json_row_2[f'field_{text_field.id}'] == 'Blue'
    assert response_json_row_2[f'field_{number_field.id}'] == 50
    assert response_json_row_2[f'field_{boolean_field.id}'] == False

    row_2.refresh_from_db()
    assert getattr(row_2, f'field_{text_field.id}') == 'Blue'
    assert getattr(row_2, f'field_{number_field.id}') == 50
    assert getattr(row_2, f'field_{boolean_field.id}') == False

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table.id,
        'row_id': row_2.id
    })
    response = api_client.patch(
        url,
        {
            f'field_{text_field.id}': None,
            f'field_{number_field.id}': None,
            f'field_{boolean_field.id}': False
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json_row_2 = response.json()
    assert response.status_code == 200
    assert response_json_row_2['id'] == row_2.id
    assert response_json_row_2[f'field_{text_field.id}'] == None
    assert response_json_row_2[f'field_{number_field.id}'] == None
    assert response_json_row_2[f'field_{boolean_field.id}'] == False

    row_2.refresh_from_db()
    assert getattr(row_2, f'field_{text_field.id}') == None
    assert getattr(row_2, f'field_{number_field.id}') == None
    assert getattr(row_2, f'field_{boolean_field.id}') == False

    table_3 = data_fixture.create_database_table(user=user)
    decimal_field = data_fixture.create_number_field(
        table=table_3, order=0, name='Price', number_type='DECIMAL',
        number_decimal_places=2
    )
    model_3 = table_3.get_model()
    row_3 = model_3.objects.create()

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table_3.id,
        'row_id': row_3.id
    })
    response = api_client.patch(
        url,
        {f'field_{decimal_field.id}': 10.22},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json[f'field_{decimal_field.id}'] == '10.22'

    row_3.refresh_from_db()
    assert getattr(row_3, f'field_{decimal_field.id}') == Decimal('10.22')


@pytest.mark.django_db
def test_delete_row(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table()
    data_fixture.create_text_field(table=table, order=0, name='Color',
                                   text_default='white')
    data_fixture.create_number_field(table=table, order=1, name='Horsepower')
    data_fixture.create_boolean_field(table=table, order=2, name='For sale')

    model = table.get_model()
    row_1 = model.objects.create()
    row_2 = model.objects.create()

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': 9999,
        'row_id': 9999
    })
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 404
    assert response.json()['error'] == 'ERROR_TABLE_DOES_NOT_EXIST'

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table.id,
        'row_id': 9999
    })
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 404
    assert response.json()['error'] == 'ERROR_ROW_DOES_NOT_EXIST'

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table_2.id,
        'row_id': row_1.id
    })
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 400
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table.id,
        'row_id': row_1.id
    })
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 204

    assert model.objects.count() == 1
    assert model.objects.all()[0].id == row_2.id

    url = reverse('api_v0:database:rows:item', kwargs={
        'table_id': table.id,
        'row_id': row_2.id
    })
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 204
    assert model.objects.count() == 0
