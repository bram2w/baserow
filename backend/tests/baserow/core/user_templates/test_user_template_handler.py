import os
import re
import threading
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, connection, transaction
from django.test.utils import override_settings
from django.utils import timezone

import pytest

from baserow.core.exceptions import TemplateDoesNotExist
from baserow.core.handler import CoreHandler
from baserow.core.import_export.handler import ImportExportHandler
from baserow.core.models import Template, Workspace
from baserow.core.user.exceptions import UserNotFound
from baserow.core.user_templates.constants import (
    USER_TEMPLATE_ICON_MAX_LENGTH,
    UserTemplateState,
)
from baserow.core.user_templates.exceptions import (
    InvalidTemplateCategory,
    InvalidTemplateIcon,
    TemplateChangedDuringUpdate,
    TemplateSlugGenerationFailed,
)
from baserow.core.user_templates.handler import (
    UserTemplateHandler,
    generate_template_slug,
)

TEST_TEMPLATES_DIR = os.path.join(settings.BASE_DIR, "../../../tests/templates")
SLUG_SUFFIX_PATH = "baserow.core.user_templates.handler.generate_slug_suffix"


def create_root(data_fixture, **kwargs):
    kwargs.setdefault("owner", data_fixture.create_user())
    kwargs.setdefault("name", "My template")
    kwargs.setdefault("description", "What it does")
    kwargs.setdefault("icon", "iconoir-view-grid")
    if "category_ids" not in kwargs:
        kwargs["category_ids"] = [data_fixture.create_template_category().id]
    kwargs.setdefault("workspace", data_fixture.create_workspace())
    return UserTemplateHandler().create_template_root(**kwargs)


def test_user_template_icon_max_length_fits_the_icon_column():
    assert USER_TEMPLATE_ICON_MAX_LENGTH == Template._meta.get_field("icon").max_length


@pytest.mark.parametrize(
    "icon",
    ["fa-table", "iconoir-", "iconoir-table extra", "iconoir-" + "a" * 25, ""],
)
def test_validate_icon_and_categories_rejects_an_invalid_icon(icon):
    with pytest.raises(InvalidTemplateIcon):
        UserTemplateHandler().validate_icon_and_categories(icon, [])


def test_generate_template_slug_format():
    for _ in range(50):
        slug = generate_template_slug("My Great Template!")
        assert re.fullmatch(r"my-great-template-[a-z0-9]{6}", slug)
        assert re.search(r"[0-9]", slug.rsplit("-", 1)[1])


def test_generate_template_slug_truncates_long_names():
    slug = generate_template_slug("word " * 30)

    assert len(slug) <= Template._meta.get_field("slug").max_length
    base = slug.rsplit("-", 1)[0]
    assert base.startswith("word-word")
    assert not base.endswith("-")


def test_generate_template_slug_without_ascii_characters():
    assert re.fullmatch(r"template-[a-z0-9]{6}", generate_template_slug("模板"))
    assert re.fullmatch(r"template-[a-z0-9]{6}", generate_template_slug("!!!"))


@pytest.mark.django_db
def test_create_template_root(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace()
    category_1 = data_fixture.create_template_category()
    category_2 = data_fixture.create_template_category()

    template = create_root(
        data_fixture,
        owner=user,
        name="Sales pipeline",
        description="Track deals",
        icon="iconoir-coins",
        category_ids=[category_1.id, category_2.id],
        workspace=workspace,
    )

    template = Template.objects.get(id=template.id)
    assert template.type == Template.Type.USER
    assert template.owner == user
    assert template.author == user
    assert template.version == 1
    assert template.root is None
    assert template.name == "Sales pipeline"
    assert template.description == "Track deals"
    assert template.icon == "iconoir-coins"
    assert template.workspace == workspace
    assert re.fullmatch(r"sales-pipeline-[a-z0-9]{6}", template.slug)
    assert set(template.categories.all()) == {category_1, category_2}
    assert template.review_state == Template.ReviewState.NOT_SUBMITTED
    assert template.public_revision is None
    assert template.shared_revision is None
    assert template.private_link_token is None
    assert not template.archive
    assert UserTemplateHandler().get_template_state(template) == (
        UserTemplateState.PRIVATE,
        None,
    )


@pytest.mark.django_db
def test_create_template_root_opens_a_workspace_checked_before(data_fixture):
    # Anyone can check the workspace while the job copies into it, e.g. through
    # the applications list of its id. The answer is cached in that process.
    workspace = data_fixture.create_workspace()
    owner = data_fixture.create_user()
    assert not Workspace.objects.get(id=workspace.id).has_openable_template(owner)

    create_root(data_fixture, owner=owner, workspace=workspace)

    # The next request loads the workspace again.
    assert Workspace.objects.get(id=workspace.id).has_openable_template(owner)


@pytest.mark.django_db
def test_create_template_root_refuses_a_deleted_owner(data_fixture):
    owner = data_fixture.create_user()
    category = data_fixture.create_template_category()

    def delete_owner(*args, **kwargs):
        # Deleted after the template was validated.
        type(owner).objects.filter(id=owner.id).delete()

    with patch.object(Template, "full_clean", delete_owner):
        with pytest.raises(UserNotFound):
            create_root(data_fixture, owner=owner, category_ids=[category.id])

    assert not Template.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_deleting_the_owner_waits_for_a_template_being_created(data_fixture):
    owner = data_fixture.create_user()
    category = data_fixture.create_template_category()
    workspace = data_fixture.create_workspace()
    created = threading.Event()
    commit = threading.Event()
    errors = []

    def in_thread(function):
        def run():
            try:
                function()
            except Exception as error:
                errors.append(error)
            finally:
                connection.close()

        thread = threading.Thread(target=run)
        thread.start()
        return thread

    def create():
        with transaction.atomic():
            create_root(
                data_fixture,
                owner=owner,
                category_ids=[category.id],
                workspace=workspace,
            )
            created.set()
            commit.wait(timeout=10)

    creator = in_thread(create)
    assert created.wait(timeout=10)
    deleter = in_thread(lambda: type(owner).objects.get(id=owner.id).delete())
    deleter.join(timeout=1)
    assert deleter.is_alive()

    commit.set()
    creator.join(timeout=10)
    deleter.join(timeout=10)

    assert errors == []
    template = Template.objects.get()
    assert template.owner_id is None
    assert template.marked_for_deletion_at is not None


@pytest.mark.django_db
def test_create_template_root_stores_archive(data_fixture, tmpdir):
    with override_settings(MEDIA_ROOT=str(tmpdir)):
        template = create_root(data_fixture, archive=ContentFile(b"zip", "a.zip"))

        template.refresh_from_db()
        assert template.archive.name.startswith("template-revisions/")
        assert template.archive.read() == b"zip"


@pytest.mark.django_db
def test_create_template_root_rejects_an_invalid_icon(data_fixture):
    with pytest.raises(InvalidTemplateIcon):
        create_root(data_fixture, icon="fa-table")

    assert not Template.objects.exists()


@pytest.mark.django_db
def test_create_template_root_rejects_missing_or_unknown_categories(data_fixture):
    category = data_fixture.create_template_category()

    with pytest.raises(InvalidTemplateCategory):
        create_root(data_fixture, category_ids=[])

    with pytest.raises(InvalidTemplateCategory):
        create_root(data_fixture, category_ids=[category.id, category.id + 100])

    assert not Template.objects.exists()


@pytest.mark.django_db
def test_create_template_root_without_categories_on_the_instance(data_fixture):
    template = create_root(data_fixture, category_ids=[])

    assert list(template.categories.all()) == []


@pytest.mark.django_db
def test_create_template_root_runs_full_clean(data_fixture):
    with pytest.raises(ValidationError) as exc_info:
        create_root(data_fixture, name="a" * 65)
    assert "name" in exc_info.value.message_dict

    with pytest.raises(ValidationError):
        create_root(data_fixture, name="")

    used_workspace = data_fixture.create_template().workspace
    with pytest.raises(ValidationError):
        create_root(data_fixture, workspace=used_workspace)

    assert Template.objects.user().count() == 0


@pytest.mark.django_db
def test_create_template_root_retries_on_slug_collision(data_fixture):
    data_fixture.create_template(slug="taken-a1b2c3")

    with patch(SLUG_SUFFIX_PATH, side_effect=["a1b2c3", "d4e5f6"]):
        template = create_root(data_fixture, name="Taken")

    assert template.slug == "taken-d4e5f6"
    assert Template.objects.get(id=template.id).categories.count() == 1


@pytest.mark.django_db
def test_create_template_root_gives_up_after_three_collisions(data_fixture):
    data_fixture.create_template(slug="taken-a1b2c3")

    with (
        patch(SLUG_SUFFIX_PATH, return_value="a1b2c3") as suffix_mock,
        pytest.raises(TemplateSlugGenerationFailed),
    ):
        create_root(data_fixture, name="Taken")

    assert suffix_mock.call_count == 3
    assert Template.objects.user().count() == 0


@pytest.mark.django_db
def test_create_template_root_reraises_other_integrity_errors(data_fixture):
    with (
        patch.object(Template, "save", side_effect=IntegrityError("other")) as save,
        pytest.raises(IntegrityError),
    ):
        create_root(data_fixture)

    assert save.call_count == 1


def revision_kwargs(data_fixture, root, **kwargs):
    kwargs.setdefault("user", root.owner)
    kwargs.setdefault("base_revision", root)
    kwargs.setdefault("name", "Next")
    kwargs.setdefault("description", "")
    kwargs.setdefault("icon", "iconoir-view-grid")
    kwargs.setdefault("category_ids", [data_fixture.create_template_category().id])
    kwargs.setdefault("workspace", data_fixture.create_workspace())
    return {"root": root, **kwargs}


@pytest.mark.django_db
def test_create_template_revision_runs_full_clean(data_fixture):
    root = data_fixture.create_user_template()
    handler = UserTemplateHandler()

    with pytest.raises(ValidationError) as exc_info:
        handler.create_template_revision(
            **revision_kwargs(data_fixture, root, name="a" * 65)
        )
    assert "name" in exc_info.value.message_dict

    with pytest.raises(ValidationError):
        handler.create_template_revision(**revision_kwargs(data_fixture, root, name=""))

    assert not Template.objects.filter(root=root).exists()


@pytest.mark.django_db(transaction=True)
def test_create_template_revision_waits_for_a_concurrent_commit(
    data_fixture, test_thread
):
    root = data_fixture.create_user_template()
    handler = UserTemplateHandler()
    first = revision_kwargs(data_fixture, root, name="First")
    concurrent = revision_kwargs(data_fixture, root, name="Concurrent")
    validate_icon_and_categories = UserTemplateHandler.validate_icon_and_categories
    calls = []
    outcome = {}

    def commit_concurrently():
        try:
            handler.create_template_revision(**concurrent)
            outcome["concurrent"] = "committed"
        except TemplateChangedDuringUpdate:
            outcome["concurrent"] = "changed"
        finally:
            connection.close()

    with test_thread(commit_concurrently) as thread:

        def validate_with_a_concurrent_commit(self, *args, **kwargs):
            calls.append(args)
            if len(calls) == 1:
                thread.start()
                # It waits for the lock on the root, held until the first commits,
                # and then sees that the template changed.
                assert not thread.thread_stopped.wait(0.3)
            return validate_icon_and_categories(self, *args, **kwargs)

        with patch.object(
            UserTemplateHandler,
            "validate_icon_and_categories",
            validate_with_a_concurrent_commit,
        ):
            handler.create_template_revision(**first)

    assert outcome == {"concurrent": "changed"}
    assert list(Template.objects.filter(root=root).values_list("name", flat=True)) == [
        "First"
    ]


@pytest.mark.django_db
def test_store_archive_tracks_the_name_given_by_the_storage(data_fixture, tmpdir):
    storage = FileSystemStorage(location=str(tmpdir))
    resource = data_fixture.create_import_export_resource(
        created_by=data_fixture.create_user(), original_name="export.zip"
    )
    storage.save(
        ImportExportHandler().export_file_path(resource.get_archive_name()),
        ContentFile(b"archive"),
    )
    taken_name = storage.save("template-revisions/taken.zip", ContentFile(b"other"))
    tracked = []

    with patch(
        "baserow.core.user_templates.handler.template_archive_upload_to",
        return_value=taken_name,
    ):
        stored_name = UserTemplateHandler()._store_archive(
            resource, storage, lambda **content: tracked.append(content)
        )

    assert stored_name != taken_name
    assert tracked == [{"archive_name": taken_name}, {"archive_name": stored_name}]
    with storage.open(stored_name) as stored_file:
        assert stored_file.read() == b"archive"


@pytest.mark.django_db
@override_settings(APPLICATION_TEMPLATES_DIR=TEST_TEMPLATES_DIR)
def test_sync_templates_installs_official_template_next_to_user_slug(
    data_fixture, tmpdir
):
    user_template = create_root(data_fixture, name="Example template")
    assert user_template.slug.startswith("example-template-")

    storage = FileSystemStorage(location=str(tmpdir), base_url="http://localhost")
    CoreHandler().sync_templates(storage=storage)

    official = Template.objects.official().get(slug="example-template")
    assert official.workspace.application_set.count() == 1
    user_template.refresh_from_db()
    assert user_template.name == "Example template"
    assert Template.objects.user().get() == user_template


@pytest.mark.django_db
def test_list_own_templates(data_fixture):
    user = data_fixture.create_user()
    other_user = data_fixture.create_user()
    now = timezone.now()

    older = data_fixture.create_user_template(user=user)
    newer = data_fixture.create_user_template(user=user)
    same_time = data_fixture.create_user_template(user=user)
    Template.objects.filter(id=older.id).update(updated_on=now - timedelta(days=2))
    Template.objects.filter(id__in=[newer.id, same_time.id]).update(updated_on=now)

    data_fixture.create_user_template_revision(newer)
    newer_latest = data_fixture.create_user_template_revision(newer)
    data_fixture.create_user_template(user=other_user)
    marked = data_fixture.create_user_template(user=user, marked_for_deletion_at=now)
    data_fixture.create_user_template_revision(marked)
    data_fixture.create_template()

    templates = list(
        CoreHandler().list_templates(user, template_type="user", owned=True)
    )

    # The latest revision of each template, ordered by the template itself.
    assert templates == [same_time, newer_latest, older]
    assert [template.get_root() for template in templates] == [
        same_time,
        newer,
        older,
    ]


@pytest.mark.django_db
def test_list_templates_puts_never_updated_templates_last(data_fixture):
    user = data_fixture.create_user()
    never_updated = data_fixture.create_template()
    official = data_fixture.create_template()
    own = data_fixture.create_user_template(user=user)
    Template.objects.filter(id=never_updated.id).update(updated_on=None)

    templates = list(CoreHandler().list_templates(user))

    assert templates == [own, official, never_updated]


@pytest.mark.django_db
def test_list_templates_owned_by_an_anonymous_user(data_fixture):
    data_fixture.create_template()

    assert list(CoreHandler().list_templates(AnonymousUser(), owned=True)) == []


@pytest.mark.django_db
def test_get_own_template(data_fixture):
    user = data_fixture.create_user()
    root = data_fixture.create_user_template(user=user)
    revision = data_fixture.create_user_template_revision(root)
    blocked = data_fixture.create_user_template(user=user, blocked_at=timezone.now())
    marked = data_fixture.create_user_template(
        user=user, marked_for_deletion_at=timezone.now()
    )
    staff = data_fixture.create_user(is_staff=True)
    handler = UserTemplateHandler()

    assert handler.get_own_template(user, root.id) == root
    assert handler.get_own_template(user, blocked.id) == blocked

    for template_user, template_id in [
        (data_fixture.create_user(), root.id),
        (staff, root.id),
        (user, revision.id),
        (user, marked.id),
        (user, data_fixture.create_template().id),
        (user, 0),
    ]:
        with pytest.raises(TemplateDoesNotExist):
            handler.get_own_template(template_user, template_id)


@pytest.mark.django_db
def test_get_latest_revision(data_fixture):
    handler = UserTemplateHandler()
    root = data_fixture.create_user_template()
    assert handler.get_latest_revision(root) == root

    data_fixture.create_user_template_revision(root)
    latest = data_fixture.create_user_template_revision(root)
    data_fixture.create_user_template_revision(data_fixture.create_user_template())

    assert handler.get_latest_revision(root) == latest


@pytest.mark.django_db
def test_get_template_state_of_a_revision(data_fixture):
    handler = UserTemplateHandler()
    root = data_fixture.create_user_template(
        review_state=Template.ReviewState.REJECTED, reject_reason="Not useful"
    )
    revision = data_fixture.create_user_template_revision(
        root, review_state=Template.ReviewState.PENDING
    )

    # The review is the revision's own.
    assert handler.get_template_state(root) == (
        UserTemplateState.REJECTED,
        "Not useful",
    )
    assert handler.get_template_state(revision) == (UserTemplateState.IN_REVIEW, None)

    # Whether it's public or blocked is the template's, so its root's.
    root.review_state = Template.ReviewState.APPROVED
    root.public_revision = root
    root.save()
    revision = Template.objects.get(id=revision.id)
    assert handler.get_template_state(revision) == (UserTemplateState.PUBLIC, None)

    root.blocked_at = timezone.now()
    root.blocked_reason = "Spam"
    root.save()
    revision = Template.objects.get(id=revision.id)
    assert handler.get_template_state(revision) == (
        UserTemplateState.BLOCKED,
        "Spam",
    )


@pytest.mark.django_db
def test_get_template_state(data_fixture):
    handler = UserTemplateHandler()
    template = data_fixture.create_user_template()

    assert handler.get_template_state(template) == (UserTemplateState.PRIVATE, None)

    template.review_state = Template.ReviewState.PENDING
    assert handler.get_template_state(template) == (
        UserTemplateState.IN_REVIEW,
        None,
    )

    template.review_state = Template.ReviewState.REJECTED
    template.reject_reason = "Not useful"
    assert handler.get_template_state(template) == (
        UserTemplateState.REJECTED,
        "Not useful",
    )

    template.review_state = Template.ReviewState.APPROVED
    template.public_revision = template
    assert handler.get_template_state(template) == (UserTemplateState.PUBLIC, None)

    template.blocked_at = timezone.now()
    template.blocked_reason = "Spam"
    assert handler.get_template_state(template) == (
        UserTemplateState.BLOCKED,
        "Spam",
    )

    template.blocked_reason = ""
    assert handler.get_template_state(template) == (UserTemplateState.BLOCKED, None)
