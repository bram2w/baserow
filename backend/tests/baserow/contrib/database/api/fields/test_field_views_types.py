import pytest
from faker import Faker
from pytz import timezone
from datetime import date, datetime

from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from django.shortcuts import reverse

from baserow.contrib.database.fields.models import (
    LongTextField, URLField, DateField, EmailField
)


@pytest.mark.django_db
def test_text_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(
        table=table,
        order=0,
        name='Old name',
        text_default='Default'
    )

    response = api_client.patch(
        reverse('api:database:fields:item', kwargs={'field_id': text_field.id}),
        {'name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json['text_default'] == 'Default'


@pytest.mark.django_db
def test_long_text_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    table = data_fixture.create_database_table(user=user)
    fake = Faker()
    text = fake.text()

    response = api_client.post(
        reverse('api:database:fields:list', kwargs={'table_id': table.id}),
        {'name': 'Long text', 'type': 'long_text'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json['type'] == 'long_text'
    assert LongTextField.objects.all().count() == 1
    field_id = response_json['id']

    response = api_client.patch(
        reverse('api:database:fields:item', kwargs={'field_id': field_id}),
        {'name': 'Long text 2'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{field_id}': text
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == text

    model = table.get_model(attribute_names=True)
    row = model.objects.all().last()
    assert row.long_text_2 == text

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{field_id}': ''
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == ''

    row = model.objects.all().last()
    assert row.long_text_2 == ''

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{field_id}': None
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == None

    row = model.objects.all().last()
    assert row.long_text_2 == None

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == None

    row = model.objects.all().last()
    assert row.long_text_2 == None

    url = reverse('api:database:fields:item', kwargs={'field_id': field_id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == HTTP_204_NO_CONTENT
    assert LongTextField.objects.all().count() == 0


@pytest.mark.django_db
def test_url_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    table = data_fixture.create_database_table(user=user)

    response = api_client.post(
        reverse('api:database:fields:list', kwargs={'table_id': table.id}),
        {'name': 'URL', 'type': 'url'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json['type'] == 'url'
    assert URLField.objects.all().count() == 1
    field_id = response_json['id']

    response = api_client.patch(
        reverse('api:database:fields:item', kwargs={'field_id': field_id}),
        {'name': 'URL2'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{field_id}': 'https://test.nl'
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == 'https://test.nl'

    model = table.get_model(attribute_names=True)
    row = model.objects.all().last()
    assert row.url2 == 'https://test.nl'

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{field_id}': ''
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == ''

    row = model.objects.all().last()
    assert row.url2 == ''

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{field_id}': None
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == ''

    row = model.objects.all().last()
    assert row.url2 == ''

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == ''

    row = model.objects.all().last()
    assert row.url2 == ''

    url = reverse('api:database:fields:item', kwargs={'field_id': field_id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == HTTP_204_NO_CONTENT
    assert URLField.objects.all().count() == 0


@pytest.mark.django_db
def test_date_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    table = data_fixture.create_database_table(user=user)

    response = api_client.post(
        reverse('api:database:fields:list', kwargs={'table_id': table.id}),
        {'name': 'Date', 'type': 'date'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json['type'] == 'date'
    assert DateField.objects.all().count() == 1
    date_field_id = response_json['id']

    response = api_client.post(
        reverse('api:database:fields:list', kwargs={'table_id': table.id}),
        {'name': 'Datetime', 'type': 'date', 'date_include_time': True},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json['type'] == 'date'
    assert DateField.objects.all().count() == 2
    date_time_field_id = response_json['id']

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{date_field_id}': '2020-04-01 12:00',
            f'field_{date_time_field_id}': '2020-04-01'
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json['error'] == 'ERROR_REQUEST_BODY_VALIDATION'
    assert response_json['detail'][f'field_{date_field_id}'][0]['code'] == 'invalid'
    assert response_json['detail'][f'field_{date_time_field_id}'][0]['code'] == \
           'invalid'

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{date_field_id}': '2020-04-01',
            f'field_{date_time_field_id}': '2020-04-01 14:30:20'
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{date_field_id}'] == '2020-04-01'
    assert response_json[f'field_{date_time_field_id}'] == '2020-04-01T14:30:20Z'

    model = table.get_model(attribute_names=True)
    row = model.objects.all().last()
    assert row.date == date(2020, 4, 1)
    assert row.datetime == datetime(2020, 4, 1, 14, 30, 20, tzinfo=timezone('UTC'))

    url = reverse('api:database:fields:item', kwargs={
        'field_id': date_time_field_id
    })
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == HTTP_204_NO_CONTENT
    assert DateField.objects.all().count() == 1


@pytest.mark.django_db
def test_email_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    table = data_fixture.create_database_table(user=user)

    response = api_client.post(
        reverse('api:database:fields:list', kwargs={'table_id': table.id}),
        {'name': 'Email', 'type': 'email'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json['type'] == 'email'
    assert EmailField.objects.all().count() == 1
    field_id = response_json['id']

    response = api_client.patch(
        reverse('api:database:fields:item', kwargs={'field_id': field_id}),
        {'name': 'Email2'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{field_id}': 'test@test.nl'
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == 'test@test.nl'

    model = table.get_model(attribute_names=True)
    row = model.objects.all().last()
    assert row.email2 == 'test@test.nl'

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{field_id}': ''
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == ''

    row = model.objects.all().last()
    assert row.email2 == ''

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {
            f'field_{field_id}': None
        },
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == ''

    row = model.objects.all().last()
    assert row.email2 == ''

    response = api_client.post(
        reverse('api:database:rows:list', kwargs={'table_id': table.id}),
        {},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == ''

    row = model.objects.all().last()
    assert row.email2 == ''

    email = reverse('api:database:fields:item', kwargs={'field_id': field_id})
    response = api_client.delete(email, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == HTTP_204_NO_CONTENT
    assert EmailField.objects.all().count() == 0
