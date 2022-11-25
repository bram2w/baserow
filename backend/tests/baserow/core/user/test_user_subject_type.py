import pytest

from baserow.core.subjects import UserSubjectType


@pytest.mark.django_db
def test_user_subject_type_is_in_group(data_fixture):
    group = data_fixture.create_group()
    user_not_in_group = data_fixture.create_user()
    user_in_group = data_fixture.create_user(group=group)
    inactive_user = data_fixture.create_user(group=group, is_active=False)
    to_be_deleted_user = data_fixture.create_user(group=group, to_be_deleted=True)

    assert UserSubjectType().is_in_group(user_not_in_group.id, group) is False
    assert UserSubjectType().is_in_group(user_in_group.id, group) is True
    assert UserSubjectType().is_in_group(9999, group) is False
    assert UserSubjectType().is_in_group(inactive_user.id, group) is False
    assert UserSubjectType().is_in_group(to_be_deleted_user.id, group) is False
