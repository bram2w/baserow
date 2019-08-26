import pytest

from django.shortcuts import reverse

from baserow.core.models import Group, GroupUser


@pytest.mark.django_db
def test_list_groups(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(
        email='test@test.nl', password='password', first_name='Test1')
    group_2 = data_fixture.create_user_group(user=user, order=2)
    group_1 = data_fixture.create_user_group(user=user, order=1)

    response = api_client.get(reverse('api_v0:groups:list'), **{
        'HTTP_AUTHORIZATION': f'JWT {token}'
    })
    assert response.status_code == 200
    response_json = response.json()
    assert response_json[0]['id'] == group_1.id
    assert response_json[0]['order'] == 1
    assert response_json[1]['id'] == group_2.id
    assert response_json[1]['order'] == 2


@pytest.mark.django_db
def test_create_group(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    response = api_client.post(reverse('api_v0:groups:list'), {
        'name': 'Test 1'
    }, format='json', HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 200
    json_response = response.json()
    group_user = GroupUser.objects.filter(user=user.id).first()
    assert group_user.order == 1
    assert group_user.order == json_response['order']
    assert group_user.group.id == json_response['id']
    assert group_user.group.name == 'Test 1'
    assert group_user.user == user

    response = api_client.post(reverse('api_v0:groups:list'), {
        'not_a_name': 'Test 1'
    }, format='json', HTTP_AUTHORIZATION=f'JWT {token}')
    assert response.status_code == 400


@pytest.mark.django_db
def test_update_group(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user, name='Old name')

    url = reverse('api_v0:groups:item', kwargs={'group_id': 99999})
    response = api_client.patch(
        url,
        {'name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404

    url = reverse('api_v0:groups:item', kwargs={'group_id': group.id})
    response = api_client.patch(
        url,
        {'name': 'New name'},
        format='json',
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 200
    json_response = response.json()

    group.refresh_from_db()

    assert group.name == 'New name'
    assert json_response['id'] == group.id
    assert json_response['name'] == 'New name'


@pytest.mark.django_db
def test_delete_group(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user, name='Old name')

    url = reverse('api_v0:groups:item', kwargs={'group_id': 99999})
    response = api_client.delete(
        url,
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 404

    url = reverse('api_v0:groups:item', kwargs={'group_id': group.id})
    response = api_client.delete(
        url,
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == 204
    assert Group.objects.all().count() == 0


@pytest.mark.django_db
def test_reorder_groups(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group_user_1 = data_fixture.create_user_group(user=user)
    group_user_2 = data_fixture.create_user_group(user=user)
    group_user_3 = data_fixture.create_user_group(user=user)

    url = reverse('api_v0:groups:order')
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
