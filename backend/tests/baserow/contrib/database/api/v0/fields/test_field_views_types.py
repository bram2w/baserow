import pytest
from faker import Faker

from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT

from django.shortcuts import reverse

from baserow.contrib.database.fields.models import LongTextField


@pytest.mark.django_db
def test_long_text_field_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    table = data_fixture.create_database_table(user=user)
    fake = Faker()
    text = fake.text()

    response = api_client.post(
        reverse('api_v0:database:fields:list', kwargs={'table_id': table.id}),
        {'name': 'Long text', 'type': 'long_text'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json['type'] == 'long_text'
    assert len(LongTextField.objects.all()) == 1
    field_id = response_json['id']

    response = api_client.patch(
        reverse('api_v0:database:fields:item', kwargs={'field_id': field_id}),
        {'name': 'Long text 2'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.post(
        reverse('api_v0:database:rows:list', kwargs={'table_id': table.id}),
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
        reverse('api_v0:database:rows:list', kwargs={'table_id': table.id}),
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
        reverse('api_v0:database:rows:list', kwargs={'table_id': table.id}),
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
        reverse('api_v0:database:rows:list', kwargs={'table_id': table.id}),
        {},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json[f'field_{field_id}'] == None

    row = model.objects.all().last()
    assert row.long_text_2 == None

    url = reverse('api_v0:database:fields:item', kwargs={'field_id': field_id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == HTTP_204_NO_CONTENT
    assert len(LongTextField.objects.all()) == 0
