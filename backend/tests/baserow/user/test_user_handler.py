import pytest

from baserow.core.models import Group
from baserow.contrib.database.models import (
    Database, Table, GridView, TextField, BooleanField
)
from baserow.user.exceptions import UserAlreadyExist
from baserow.user.handler import UserHandler


@pytest.mark.django_db
def test_create_user():
    user_handler = UserHandler()

    user = user_handler.create_user('Test1', 'test@test.nl', 'password')
    assert user.pk
    assert user.first_name == 'Test1'
    assert user.email == 'test@test.nl'
    assert user.username == 'test@test.nl'

    assert Group.objects.all().count() == 1
    group = Group.objects.all().first()
    assert group.users.filter(id=user.id).count() == 1
    assert group.name == "Test1's group"

    assert Database.objects.all().count() == 1
    assert Table.objects.all().count() == 2
    assert GridView.objects.all().count() == 2
    assert TextField.objects.all().count() == 3
    assert BooleanField.objects.all().count() == 2

    tables = Table.objects.all().order_by('id')

    model_1 = tables[0].get_model()
    assert model_1.objects.all().count() == 4

    model_2 = tables[1].get_model()
    assert model_2.objects.all().count() == 3

    with pytest.raises(UserAlreadyExist):
        user_handler.create_user('Test1', 'test@test.nl', 'password')
