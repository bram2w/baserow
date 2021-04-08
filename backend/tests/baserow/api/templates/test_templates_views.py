import pytest
import os

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from django.shortcuts import reverse
from django.conf import settings

from baserow.core.handler import CoreHandler
from baserow.core.models import Template, Application


@pytest.mark.django_db
def test_list_templates(api_client, data_fixture):
    category_1 = data_fixture.create_template_category(name='Cat 1')
    category_3 = data_fixture.create_template_category(name='Cat 3')
    category_2 = data_fixture.create_template_category(name='Cat 2')

    template_1 = data_fixture.create_template(
        name='Template 1',
        icon='document',
        category=category_1,
        keywords='test1,test2',
        slug='project-management'
    )
    template_2 = data_fixture.create_template(
        name='Template 2',
        icon='document',
        category=category_2,
    )
    template_3 = data_fixture.create_template(
        name='Template 3',
        icon='document',
        categories=[category_2, category_3]
    )

    response = api_client.get(reverse('api:templates:list'))
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 3
    assert response_json[0]['id'] == category_1.id
    assert response_json[0]['name'] == 'Cat 1'
    assert len(response_json[0]['templates']) == 1
    assert response_json[0]['templates'][0]['id'] == template_1.id
    assert response_json[0]['templates'][0]['name'] == template_1.name
    assert response_json[0]['templates'][0]['icon'] == template_1.icon
    assert response_json[0]['templates'][0]['keywords'] == 'test1,test2'
    assert response_json[0]['templates'][0]['group_id'] == template_1.group_id
    assert response_json[0]['templates'][0]['is_default'] is True
    assert len(response_json[1]['templates']) == 2
    assert response_json[1]['templates'][0]['id'] == template_2.id
    assert response_json[1]['templates'][0]['is_default'] is False
    assert response_json[1]['templates'][1]['id'] == template_3.id
    assert response_json[1]['templates'][1]['is_default'] is False
    assert len(response_json[2]['templates']) == 1
    assert response_json[2]['templates'][0]['id'] == template_3.id
    assert response_json[2]['templates'][0]['is_default'] is False


@pytest.mark.django_db
def test_install_template(api_client, data_fixture):
    old_templates = settings.APPLICATION_TEMPLATES_DIR
    settings.APPLICATION_TEMPLATES_DIR = os.path.join(
        settings.BASE_DIR,
        '../../../tests/templates'
    )

    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    group_2 = data_fixture.create_group()

    handler = CoreHandler()
    handler.sync_templates()

    template_2 = data_fixture.create_template(slug='does-not-exist')
    template = Template.objects.get(slug='example-template')

    response = api_client.get(
        reverse('api:templates:install', kwargs={
            'group_id': group.id,
            'template_id': template_2.id
        }),
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'ERROR_TEMPLATE_FILE_DOES_NOT_EXIST'

    response = api_client.get(
        reverse('api:templates:install', kwargs={
            'group_id': group_2.id,
            'template_id': template.id
        }),
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'ERROR_USER_NOT_IN_GROUP'

    response = api_client.get(
        reverse('api:templates:install', kwargs={
            'group_id': 0,
            'template_id': template.id
        }),
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()['error'] == 'ERROR_GROUP_DOES_NOT_EXIST'

    response = api_client.get(
        reverse('api:templates:install', kwargs={
            'group_id': group.id,
            'template_id': 0
        }),
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()['error'] == 'ERROR_TEMPLATE_DOES_NOT_EXIST'

    response = api_client.get(
        reverse('api:templates:install', kwargs={
            'group_id': group.id,
            'template_id': template.id
        }),
        HTTP_AUTHORIZATION=f'JWT {token}'
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()

    assert len(response_json) == 1
    assert response_json[0]['group']['id'] == group.id
    application = Application.objects.all().order_by('id').last()
    assert response_json[0]['id'] == application.id
    assert response_json[0]['group']['id'] == application.group_id

    settings.APPLICATION_TEMPLATES_DIR = old_templates
