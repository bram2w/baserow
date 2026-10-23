import uuid

from django.core.files.base import ContentFile
from django.db import connection
from django.db.models import Q
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

import pytest

from baserow.core.exceptions import (
    TemplateDoesNotExist,
    TemplateFileDoesNotExist,
)
from baserow.core.models import Template
from baserow.core.storage import get_default_storage
from baserow.core.user_templates.exceptions import (
    TemplateBlocked,
    TemplateHasNoContent,
)
from baserow.core.user_templates.handler import UserTemplateHandler
from baserow.core.user_templates.service import UserTemplateService

pytestmark = pytest.mark.usefixtures("use_tmp_media_root")


def _store_archive(template):
    """Stores a small archive in the storage and sets it on the template."""

    name = get_default_storage().save(
        f"template-revisions/{uuid.uuid4().hex}.zip", ContentFile(b"archive")
    )
    Template.objects.filter(id=template.id).update(archive=name)
    template.refresh_from_db()
    return name


def _create_template(data_fixture, owner=None, *, public=False, **changes):
    """
    A user template with a database and an archive in its only revision, public
    when asked.
    """

    root = data_fixture.create_user_template(user=owner)
    data_fixture.create_database_application(workspace=root.workspace)
    _store_archive(root)
    if public:
        changes.update(public_revision=root, review_state=Template.ReviewState.APPROVED)
    if changes:
        Template.objects.filter(id=root.id).update(**changes)
        root.refresh_from_db()
    return root


def _add_revision(data_fixture, root, **kwargs):
    revision = data_fixture.create_user_template_revision(root, **kwargs)
    data_fixture.create_database_application(workspace=revision.workspace)
    _store_archive(revision)
    return revision


def _download(user, template, latest=False):
    return UserTemplateHandler().get_template_download(user, template.id, latest)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "latest_review_state",
    [Template.ReviewState.PENDING, Template.ReviewState.REJECTED],
)
def test_get_template_download_of_the_revision_install_copies(
    data_fixture, latest_review_state
):
    owner = data_fixture.create_user()
    viewer = data_fixture.create_user()
    root = _create_template(data_fixture, owner, public=True)
    latest = _add_revision(data_fixture, root, review_state=latest_review_state)

    # Everyone gets the public revision, and the owner the latest one when asked.
    assert _download(owner, root).archive_name == root.archive.name
    assert _download(viewer, root).archive_name == root.archive.name
    assert _download(owner, root, latest=True).archive_name == latest.archive.name
    assert latest.archive.name != root.archive.name
    with pytest.raises(TemplateDoesNotExist):
        _download(viewer, root, latest=True)


@pytest.mark.django_db
def test_get_template_download_of_a_details_only_revision(data_fixture):
    owner = data_fixture.create_user()
    root = _create_template(data_fixture, owner)
    # A details-only update shares the content and the archive of the revision.
    latest = data_fixture.create_user_template_revision(
        root, name="Renamed", workspace=root.workspace, archive=root.archive.name
    )

    download = _download(owner, root)

    assert download.archive_name == root.archive.name
    assert download.file_name == "renamed.zip"
    assert download.url_workspace_id == latest.workspace_id


@pytest.mark.django_db
def test_get_template_download_of_something_else_than_a_user_template_root(
    data_fixture,
):
    owner = data_fixture.create_user()
    viewer = data_fixture.create_user()
    root = _create_template(data_fixture, owner, public=True)
    revision = _add_revision(data_fixture, root)
    official = data_fixture.create_template()
    data_fixture.create_database_application(workspace=official.workspace)
    _store_archive(official)
    marked = _create_template(
        data_fixture, owner, marked_for_deletion_at=timezone.now()
    )

    for user, template in [
        (owner, revision),
        (viewer, revision),
        (owner, official),
        (owner, marked),
    ]:
        for latest in [False, True]:
            with pytest.raises(TemplateDoesNotExist):
                _download(user, template, latest)

    with pytest.raises(TemplateDoesNotExist):
        UserTemplateHandler().get_template_download(owner, 0)


@pytest.mark.django_db
def test_get_template_download_follows_the_install_access(data_fixture):
    owner = data_fixture.create_user()
    stranger = data_fixture.create_user()
    private = _create_template(data_fixture, owner)
    blocked = _create_template(
        data_fixture, owner, public=True, blocked_at=timezone.now()
    )

    with pytest.raises(TemplateBlocked):
        _download(owner, blocked)
    with pytest.raises(TemplateDoesNotExist):
        _download(stranger, blocked)
    with pytest.raises(TemplateDoesNotExist):
        _download(stranger, private)
    with pytest.raises(TemplateDoesNotExist):
        UserTemplateService().get_template_download(stranger, private.id)


@pytest.mark.django_db
def test_get_template_download_without_archive(data_fixture):
    owner = data_fixture.create_user()
    stranger = data_fixture.create_user()
    without_archive = _create_template(data_fixture, owner)
    Template.objects.filter(id=without_archive.id).update(archive="")
    removed_archive = _create_template(data_fixture, owner)
    get_default_storage().delete(removed_archive.archive.name)

    for template in [without_archive, removed_archive]:
        with pytest.raises(TemplateFileDoesNotExist):
            _download(owner, template)
        # Whether the file exists is only told to who has access.
        with pytest.raises(TemplateDoesNotExist):
            _download(stranger, template)


@pytest.mark.django_db
def test_get_template_download_without_content(data_fixture):
    owner = data_fixture.create_user()
    pruned = _create_template(data_fixture, owner, pruned_at=timezone.now())

    with pytest.raises(TemplateHasNoContent):
        _download(owner, pruned)


@pytest.mark.django_db
def test_get_template_download_url_workspace(data_fixture):
    owner = data_fixture.create_user()
    viewer = data_fixture.create_user()
    root = _create_template(data_fixture, owner, public=True)
    latest = _add_revision(data_fixture, root)

    # The workspace of the downloaded revision.
    assert _download(owner, root).url_workspace_id == root.workspace_id
    assert _download(viewer, root).url_workspace_id == root.workspace_id
    assert _download(owner, root, latest=True).url_workspace_id == (latest.workspace_id)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name,file_name",
    [("Sales pipeline", "sales-pipeline.zip"), ("!!!", "template.zip")],
)
def test_get_template_download_file_name(data_fixture, name, file_name):
    owner = data_fixture.create_user()
    root = _create_template(data_fixture, owner, name=name)

    assert _download(owner, root).file_name == file_name


@pytest.mark.django_db
def test_get_template_download_writes_nothing(data_fixture):
    owner = data_fixture.create_user()
    viewer = data_fixture.create_user()
    root = _create_template(data_fixture, owner, public=True)
    _add_revision(data_fixture, root)
    fields = ["install_count", "updated_on", "public_revision_id", "shared_revision_id"]

    def snapshot():
        return list(
            Template.objects.filter(Q(id=root.id) | Q(root=root))
            .order_by("id")
            .values(*fields)
        )

    before = snapshot()
    with CaptureQueriesContext(connection) as queries:
        for user, latest in [(owner, False), (owner, True), (viewer, False)]:
            _download(user, root, latest)

    assert snapshot() == before
    writes = [
        query["sql"]
        for query in queries.captured_queries
        if query["sql"].lstrip().upper().startswith(("UPDATE", "INSERT", "DELETE"))
    ]
    assert writes == []
