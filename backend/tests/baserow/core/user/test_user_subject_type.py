from typing import NamedTuple

import pytest

from baserow.core.subjects import UserSubjectType


@pytest.mark.django_db
def test_user_subject_type_is_in_group(data_fixture):
    group = data_fixture.create_group()
    user_not_in_group = data_fixture.create_user()
    user_in_group = data_fixture.create_user(group=group)
    inactive_user = data_fixture.create_user(group=group, is_active=False)
    to_be_deleted_user = data_fixture.create_user(group=group, to_be_deleted=True)

    class FakeUser(NamedTuple):
        id: int

    fake_user = FakeUser(9999999)

    assert UserSubjectType().is_in_group(user_not_in_group, group) is False
    assert UserSubjectType().is_in_group(user_in_group, group) is True
    assert UserSubjectType().is_in_group(fake_user, group) is False
    assert UserSubjectType().is_in_group(inactive_user, group) is False
    assert UserSubjectType().is_in_group(to_be_deleted_user, group) is False

    assert UserSubjectType().are_in_group(
        [
            user_not_in_group,
            user_in_group,
            fake_user,
            inactive_user,
            to_be_deleted_user,
        ],
        group,
    ) == [False, True, False, False, False]


@pytest.mark.django_db
def test_user_subject_get_users_included_in_subject(data_fixture):
    user = data_fixture.create_user()
    assert UserSubjectType().get_users_included_in_subject(user) == [user]
