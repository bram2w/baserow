from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.utils import timezone

import pytest
from freezegun import freeze_time

from baserow.core.admin.users.handler import UserAdminHandler
from baserow.core.models import Template
from baserow.core.user.handler import UserHandler

User = get_user_model()


@pytest.mark.django_db
def test_deleting_user_marks_their_user_templates_for_deletion(data_fixture):
    user = data_fixture.create_user()
    other_user = data_fixture.create_user()
    template = data_fixture.create_user_template(user=user)
    revision = data_fixture.create_user_template_revision(template)
    other_template = data_fixture.create_user_template(user=other_user)

    user.delete()

    template.refresh_from_db()
    assert template.owner is None
    assert template.author is None
    assert template.marked_for_deletion_at is not None
    revision.refresh_from_db()
    assert revision.marked_for_deletion_at is None
    other_template.refresh_from_db()
    assert other_template.owner == other_user
    assert other_template.marked_for_deletion_at is None


@pytest.mark.django_db
def test_deleting_user_keeps_earlier_deletion_mark(data_fixture):
    user = data_fixture.create_user()
    marked_on = timezone.now() - timedelta(days=1)
    template = data_fixture.create_user_template(
        user=user, marked_for_deletion_at=marked_on
    )

    user.delete()

    template.refresh_from_db()
    assert template.marked_for_deletion_at == marked_on


@pytest.mark.django_db
def test_deleting_user_doesnt_touch_official_templates(data_fixture):
    user = data_fixture.create_user()
    official = data_fixture.create_template()

    user.delete()

    official.refresh_from_db()
    assert official.marked_for_deletion_at is None


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_can_delete_user_owning_a_user_template(data_fixture):
    admin = data_fixture.create_user(is_staff=True)
    user = data_fixture.create_user()
    template = data_fixture.create_user_template(user=user)

    UserAdminHandler().delete_user(admin, user.id)

    assert not User.objects.filter(id=user.id).exists()
    template.refresh_from_db()
    assert template.owner is None
    assert template.marked_for_deletion_at is not None


@pytest.mark.django_db
def test_scheduled_user_deletion_deletes_template_owner_and_other_user(
    data_fixture,
):
    owner = data_fixture.create_user()
    other_user = data_fixture.create_user()
    template = data_fixture.create_user_template(user=owner)

    for user in (owner, other_user):
        user.profile.to_be_deleted = True
        user.profile.save(update_fields=("to_be_deleted",))

    handler = UserHandler()
    with freeze_time("2020-01-01 12:00"):
        handler.update_last_login(owner)
        handler.update_last_login(other_user)

    with freeze_time("2020-01-07 12:00"):
        handler.delete_expired_users_and_related_workspaces_if_last_admin(
            grace_delay=timedelta(days=3)
        )

    assert not User.objects.filter(id__in=[owner.id, other_user.id]).exists()
    template = Template.objects.get(id=template.id)
    assert template.owner is None
    assert template.marked_for_deletion_at is not None
