import pytest

from baserow.core.models import UserFile
from baserow.core.user_files.exceptions import InvalidUserFileNameError


@pytest.mark.django_db
def test_user_file_name(data_fixture):
    user_file = data_fixture.create_user_file()
    user_file_2 = data_fixture.create_user_file()
    user_file_3 = data_fixture.create_user_file()

    with pytest.raises(InvalidUserFileNameError):
        UserFile.objects.all().name("wrong.jpg")

    queryset = UserFile.objects.all().name(user_file.name)
    assert len(queryset) == 1
    assert queryset[0].id == user_file.id

    queryset = UserFile.objects.all().name(user_file_2.name)
    assert len(queryset) == 1
    assert queryset[0].id == user_file_2.id

    queryset = UserFile.objects.all().name(user_file.name, user_file_2.name)
    assert len(queryset) == 2
    assert queryset[0].id == user_file.id
    assert queryset[1].id == user_file_2.id

    queryset = UserFile.objects.all().name(user_file_3.name, user_file.name)
    assert len(queryset) == 2
    assert queryset[0].id == user_file.id
    assert queryset[1].id == user_file_3.id
