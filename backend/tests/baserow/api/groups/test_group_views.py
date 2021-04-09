import pytest

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from django.shortcuts import reverse

from baserow.core.models import Group, GroupUser


@pytest.mark.django_db
def test_list_groups(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    user_group_2 = data_fixture.create_user_group(user=user, order=2)
    user_group_1 = data_fixture.create_user_group(user=user, order=1)
    data_fixture.create_group()

    response = api_client.get(reverse('api:groups:list'), **{
        'HTTP_AUTHORIZATION': f'JWT {token}'
    })
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 2
    assert response_json[0]['id'] == user_group_1.group.id
    assert response_json[0]['order'] == 1
    assert response_json[1]['id'] == user_group_2.group.id
    assert response_json[1]['order'] == 2


@pytest.mark.django_db
def test_create_group(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    response = api_client.post(reverse('api:groups:list'), {
        'name': 'Test 1'
    }, format='json', HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == HTTP_200_OK
    json_response = response.json()
    group_user = GroupUser.objects.filter(user=user.id).first()
    assert group_user.order == 1
    assert group_user.order == json_response['order']
    assert group_user.group.id == json_response['id']
    assert group_user.group.name == 'Test 1'
    assert group_user.user == user

    response = api_client.post(reverse('api:groups:list'), {
        'not_a_name': 'Test 1'
    }, format='json', HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_group(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user, name='Old name')
    data_fixture.create_user_group(user=user_2, group=group, permissions='MEMBER')
    group_2 = data_fixture.create_group()

    url = reverse('api:groups:item', kwargs={'group_id': 99999})
    response = api_client.patch(
        url,
        {'name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()['error'] == 'ERROR_GROUP_DOES_NOT_EXIST'

    url = reverse('api:groups:item', kwargs={'group_id': group_2.id})
    response = api_client.patch(
        url,
        {'name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api:groups:item', kwargs={'group_id': group.id})
    response = api_client.patch(
        url,
        {'name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token_2}'
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'ERROR_USER_INVALID_GROUP_PERMISSIONS'

    url = reverse('api:groups:item', kwargs={'group_id': group.id})
    response = api_client.patch(
        url,
        {'name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_200_OK
    json_response = response.json()

    group.refresh_from_db()

    assert group.name == 'New name'
    assert json_response['id'] == group.id
    assert json_response['name'] == 'New name'


@pytest.mark.django_db
def test_delete_group(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    user_2, token_2 = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user, name='Old name')
    data_fixture.create_user_group(user=user_2, group=group, permissions='MEMBER')
    group_2 = data_fixture.create_group()

    url = reverse('api:groups:item', kwargs={'group_id': 99999})
    response = api_client.delete(
        url,
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()['error'] == 'ERROR_GROUP_DOES_NOT_EXIST'

    url = reverse('api:groups:item', kwargs={'group_id': group_2.id})
    response = api_client.delete(
        url,
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    url = reverse('api:groups:item', kwargs={'group_id': group.id})
    response = api_client.delete(
        url,
        HTTP_AUTHORIZATION=f'JWT {token_2}'
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'ERROR_USER_INVALID_GROUP_PERMISSIONS'

    url = reverse('api:groups:item', kwargs={'group_id': group.id})
    response = api_client.delete(
        url,
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 204
    assert Group.objects.all().count() == 1


@pytest.mark.django_db
def test_reorder_groups(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group_user_1 = data_fixture.create_user_group(user=user)
    group_user_2 = data_fixture.create_user_group(user=user)
    group_user_3 = data_fixture.create_user_group(user=user)

    url = reverse('api:groups:order')
    response = api_client.post(
        url,
        {'groups': [group_user_2.group.id, group_user_1.group.id,
                    group_user_3.group.id]},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 204

    group_user_1.refresh_from_db()
    group_user_2.refresh_from_db()
    group_user_3.refresh_from_db()

    assert [1, 2, 3] == [group_user_2.order, group_user_1.order, group_user_3.order]
