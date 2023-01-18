import pytest

from baserow.contrib.database.models import Database
from baserow.contrib.database.plugins import DatabasePlugin


@pytest.mark.django_db
def test_user_created_without_group_returns(data_fixture):
    # If the user registered without being invited, and the Setting
    # `allow_global_group_creation` is set to `False`, then no `Group` will
    # be created for this `user`.
    plugin = DatabasePlugin()
    user = data_fixture.create_user()
    assert plugin.user_created(user) is None
    assert Database.objects.count() == 0


@pytest.mark.django_db
def test_user_created_with_invitation_or_template_returns(data_fixture):
    # If the user created an account in combination with a group invitation we
    # don't want to create the initial data in the group because data should
    # already exist.
    plugin = DatabasePlugin()
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)

    invitation = data_fixture.create_group_invitation(group=group)
    assert plugin.user_created(user, group, invitation) is None
    assert Database.objects.count() == 0

    template = data_fixture.create_template(group=group)
    assert plugin.user_created(user, group, template=template) is None
    assert Database.objects.count() == 0


@pytest.mark.django_db
def test_user_created_with_group_without_invitation_or_template_creates_dummy_data(
    data_fixture,
):
    # If the user creates an account, without being invited, then we'll create
    # two tables with dummy data in their initial group's application.
    plugin = DatabasePlugin()
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    plugin.user_created(user, group)
    assert Database.objects.count() == 1
    database = Database.objects.get()
    assert database.table_set.count() == 2
