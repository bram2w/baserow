import pytest

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

    with pytest.raises(UserAlreadyExist):
        user_handler.create_user('Test1', 'test@test.nl', 'password')
