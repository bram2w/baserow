import secrets
import string
from datetime import timedelta
from typing import Callable, Iterable, List, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.files import File
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from loguru import logger

from baserow.core.import_export.handler import ImportExportHandler
from baserow.core.jobs.constants import JOB_CANCELLED, JOB_FAILED
from baserow.core.models import (
    Application,
    ImportExportResource,
    Template,
    TemplateCategory,
    Workspace,
    template_archive_upload_to,
)
from baserow.core.registries import ImportExportConfig
from baserow.core.storage import get_default_storage
from baserow.core.trash.handler import TrashHandler
from baserow.core.user.exceptions import UserNotFound
from baserow.core.user_templates.constants import (
    USER_TEMPLATE_ICON_MAX_LENGTH,
    USER_TEMPLATE_ICON_REGEX,
    UserTemplateState,
)
from baserow.core.user_templates.exceptions import (
    InvalidTemplateCategory,
    InvalidTemplateIcon,
    TemplateSlugGenerationFailed,
)
from baserow.core.utils import ChildProgressBuilder

User = get_user_model()

SLUG_SUFFIX_LENGTH = 6
SLUG_SUFFIX_ALPHABET = string.ascii_lowercase + string.digits
# Leaves room for the `-` and the suffix within the 50 characters of `Template.slug`.
SLUG_BASE_MAX_LENGTH = 43
SLUG_MAX_ATTEMPTS = 3
UNIQUE_ROOT_SLUG_CONSTRAINT = "core_template_unique_root_slug"


def generate_slug_suffix() -> str:
    """
    Returns 6 random base36 characters with at least one digit, so the suffix never
    reads as a word.
    """

    while True:
        suffix = "".join(
            secrets.choice(SLUG_SUFFIX_ALPHABET) for _ in range(SLUG_SUFFIX_LENGTH)
        )
        if any(char.isdigit() for char in suffix):
            return suffix


def generate_template_slug(name: str) -> str:
    """
    Returns a slug for a user template. The random suffix keeps it apart from the
    official template slugs, which are file names.
    """

    base = slugify(name)[:SLUG_BASE_MAX_LENGTH].strip("-") or "template"
    return f"{base}-{generate_slug_suffix()}"


def _mark_resource_for_deletion(resource: ImportExportResource) -> None:
    resource.marked_for_deletion = True
    resource.save(update_fields=["marked_for_deletion"])


def _is_unique_root_slug_violation(error: IntegrityError) -> bool:
    diag = getattr(error.__cause__, "diag", None)
    return getattr(diag, "constraint_name", None) == UNIQUE_ROOT_SLUG_CONSTRAINT


class UserTemplateHandler:
    def validate_icon_and_categories(
        self, icon: str, category_ids: Iterable[int]
    ) -> list[TemplateCategory]:
        """
        Checks the icon and the categories chosen for a user template.

        :param icon: The icon class name, an iconoir class.
        :param category_ids: The ids of the existing categories, at least one
            unless the instance has none, like one that never synced templates.
        :raises InvalidTemplateIcon: If the icon isn't allowed.
        :raises InvalidTemplateCategory: If no category is given while there are
            some, or one of them doesn't exist.
        :return: The categories.
        """

        if len(
            icon
        ) > USER_TEMPLATE_ICON_MAX_LENGTH or not USER_TEMPLATE_ICON_REGEX.fullmatch(
            icon
        ):
            raise InvalidTemplateIcon(f"The icon {icon} is not allowed.")

        category_ids = set(category_ids)
        if not category_ids:
            if TemplateCategory.objects.exists():
                raise InvalidTemplateCategory("At least one category is required.")
            return []

        categories = list(TemplateCategory.objects.filter(id__in=category_ids))
        if len(categories) != len(category_ids):
            raise InvalidTemplateCategory("The categories are invalid.")

        return categories

    def create_template_root(
        self,
        *,
        owner: AbstractUser,
        name: str,
        description: str,
        icon: str,
        category_ids: Iterable[int],
        workspace: Workspace,
        archive: Optional[File | str] = None,
    ) -> Template:
        """
        Creates a private user template, which is a root holding revision 1. This is
        the only place where user templates are created.

        :param owner: The user who creates the template. They become its owner and
            author.
        :param name: The name of the template.
        :param description: The description of the template.
        :param icon: The icon class name, an iconoir class.
        :param category_ids: The ids of the existing categories of the template, at
            least one.
        :param workspace: The workspace holding the content of the template.
        :param archive: The downloadable file of the template, or the name of a
            file already in the storage.
        :raises InvalidTemplateIcon: If the icon isn't allowed.
        :raises InvalidTemplateCategory: If no category is given, or one of them
            doesn't exist.
        :raises ValidationError: If the template isn't valid.
        :raises TemplateSlugGenerationFailed: If no free slug was found.
        :raises UserNotFound: If the owner was deleted.
        :return: The created template.
        """

        categories = self.validate_icon_and_categories(icon, category_ids)

        template = Template(
            type=Template.Type.USER,
            owner=owner,
            author=owner,
            version=1,
            root=None,
            name=name,
            description=description,
            icon=icon,
            workspace=workspace,
            archive=archive,
        )
        # The slug is generated by us. Its uniqueness is left to the database, so a
        # slug taken in the meantime can be retried below. `open_application` is
        # nullable but not blank, and null opens the first application.
        template.full_clean(exclude=["slug", "open_application"])

        with transaction.atomic():
            if not self._lock_user(owner):
                raise UserNotFound("The owner of the template was deleted.")

            for _ in range(SLUG_MAX_ATTEMPTS):
                template.slug = generate_template_slug(name)
                try:
                    with transaction.atomic():
                        template.save()
                    break
                except IntegrityError as error:
                    if not _is_unique_root_slug_violation(error):
                        raise
            else:
                raise TemplateSlugGenerationFailed(
                    "No free slug was found for the template."
                )

            template.categories.set(categories)
            # The template types of a workspace are cached by `updated_on`, which
            # tells every process that this workspace is a template now.
            workspace.save(update_fields=["updated_on"])

        return template

    def copy_applications(
        self,
        owner: AbstractUser,
        applications: List[Application],
        *,
        name: str,
        progress_builder: Optional[ChildProgressBuilder] = None,
        track_content: Optional[Callable[..., None]] = None,
    ) -> Tuple[Workspace, str]:
        """
        Copies the applications into a new workspace nobody is a member of and
        stores an archive of the copy, which together become the content of a user
        template.

        The export and the import run their own transactions, so nothing is rolled
        back if it fails. `track_content` is called with the `template_workspace`
        and then with the `archive_name` as soon as they exist, so that the caller
        can remove them with `delete_content_without_template`.

        :param owner: The user who creates the template.
        :param applications: The applications copied into the template.
        :param name: The name of the template, also given to the workspace.
        :param progress_builder: A progress builder that allows for publishing
            progress.
        :param track_content: Called with the content created so far as keyword
            arguments.
        :return: The workspace holding the copy and the name of the stored archive.
        """

        if track_content is None:

            def track_content(**content):
                pass

        progress = ChildProgressBuilder.build(progress_builder, child_total=100)
        storage = get_default_storage()
        import_export_handler = ImportExportHandler()
        # Nobody is a member of the new workspace, so the import drops what
        # belongs to the users of the source: personal views and collaborators.
        config = ImportExportConfig(
            include_permission_data=False,
            reduce_disk_space_usage=True,
            workspace_for_user_references=None,
            is_duplicate=False,
            is_user_template=True,
            exclude_sensitive_data=True,
        )

        workspace = Workspace.objects.create(name=name)
        track_content(template_workspace=workspace)

        resource = import_export_handler.export_workspace_applications(
            applications,
            config,
            storage=storage,
            progress_builder=progress.create_child_builder(represents_progress=40),
        )
        try:
            import_export_handler.import_applications_from_export(
                owner,
                workspace,
                resource,
                config,
                storage=storage,
                progress_builder=progress.create_child_builder(represents_progress=40),
            )
        finally:
            _mark_resource_for_deletion(resource)

        archive_resource = import_export_handler.export_workspace_applications(
            list(workspace.application_set.all()),
            config,
            storage=storage,
            progress_builder=progress.create_child_builder(represents_progress=20),
        )
        try:
            archive_name = self._store_archive(archive_resource, storage, track_content)
        finally:
            _mark_resource_for_deletion(archive_resource)

        return workspace, archive_name

    def _store_archive(
        self,
        resource: ImportExportResource,
        storage,
        track_content: Callable[..., None],
    ) -> str:
        """
        Copies an export to where the template archives are kept. The name is
        tracked before the file is written, so that a failure leaves nothing
        untracked behind.
        """

        export_path = ImportExportHandler().export_file_path(
            resource.get_archive_name()
        )
        archive_name = template_archive_upload_to(None, None)
        track_content(archive_name=archive_name)

        with storage.open(export_path, "rb") as export_file:
            stored_name = storage.save(archive_name, export_file)

        if stored_name != archive_name:
            track_content(archive_name=stored_name)

        return stored_name

    def _lock_user(self, user: AbstractUser) -> bool:
        """
        Locks the row of the user until the end of the transaction. Creating a
        template and deleting its owner both lock it, so that a template is either
        committed before the deletion marks it, or not created at all.

        :return: Whether the user still exists.
        """

        return User.objects.select_for_update().filter(id=user.id).exists()

    def mark_owned_templates_for_deletion(self, user: AbstractUser) -> None:
        """
        Marks the user templates owned by the user for deletion. The templates
        themselves are removed later. Must run in the transaction deleting the
        user, see `_lock_user`.
        """

        self._lock_user(user)
        Template.objects.user().filter(
            owner=user, root__isnull=True, marked_for_deletion_at__isnull=True
        ).update(marked_for_deletion_at=timezone.now())

    def get_template_state(
        self, template: Template
    ) -> tuple[UserTemplateState, Optional[str]]:
        """
        Returns the state of a user template as shown to its author, together with
        the reason given by an admin for a rejected or blocked template.
        """

        if template.blocked_at is not None:
            return UserTemplateState.BLOCKED, template.blocked_reason or None
        if template.public_revision_id is not None:
            return UserTemplateState.PUBLIC, None
        if template.review_state == Template.ReviewState.PENDING:
            return UserTemplateState.IN_REVIEW, None
        if template.review_state == Template.ReviewState.REJECTED:
            return UserTemplateState.REJECTED, template.reject_reason or None
        return UserTemplateState.PRIVATE, None

    def delete_content_without_template(
        self, workspace_id: Optional[int], archive_name: str
    ) -> None:
        """
        Permanently deletes the workspace and the archive copied by a create job,
        unless a template points at them. A job that didn't create its template
        leaves them behind. Deleting twice does nothing.

        :param workspace_id: The id of the workspace holding the copy, if any.
        :param archive_name: The name of the stored archive, if any.
        """

        if (
            workspace_id is not None
            and not Template.objects.filter(workspace_id=workspace_id).exists()
        ):
            # It's called from the job hooks and the sweep, which run without a
            # transaction, and the deletion locks rows.
            with transaction.atomic():
                workspace = Workspace.objects_and_trash.filter(id=workspace_id).first()
                if workspace is not None:
                    TrashHandler.permanently_delete(workspace)

        if archive_name and not Template.objects.filter(archive=archive_name).exists():
            storage = get_default_storage()
            if storage.exists(archive_name):
                storage.delete(archive_name)

    def delete_content_of_deleted_job(
        self, workspace_id: Optional[int], archive_name: str
    ) -> None:
        """
        Deletes the workspace and the archive of a create job that is deleted, once
        the transaction deleting it commits. They're kept track of until then, and
        until their deletion succeeds, so that the sweep retries a failed one.

        :param workspace_id: The id of the workspace holding the copy, if any.
        :param archive_name: The name of the stored archive, if any.
        """

        from baserow.core.user_templates.models import UserTemplateContentToDelete

        if workspace_id is None and not archive_name:
            return

        content = UserTemplateContentToDelete.objects.create(
            workspace_id=workspace_id, archive_name=archive_name
        )
        transaction.on_commit(lambda: self._delete_tracked_content(content))

    def _delete_tracked_content(self, content) -> None:
        """
        Deletes the content a `UserTemplateContentToDelete` keeps track of, and the
        row once it's gone. A failure is logged, so that it doesn't stop deleting
        the rest, and the row is kept for the next sweep.
        """

        try:
            self.delete_content_without_template(
                content.workspace_id, content.archive_name
            )
        except Exception:
            logger.exception(f"Deleting the user template content {content.id} failed.")
            return
        content.delete()

    def delete_content_of_unfinished_jobs(self) -> None:
        """
        Deletes what the failed and cancelled create jobs left behind. It covers a
        job that was failed after its worker was killed, which no job hook sees,
        and retries what a deleted job left, see `delete_content_of_deleted_job`.

        A cancelled job is only cleaned up once its worker can't be running anymore,
        because the worker notices the cancellation late and cleans up itself.
        """

        from baserow.core.user_templates.models import (
            CreateUserTemplateJob,
            UserTemplateContentToDelete,
        )

        # The worker of a job is killed at the latest after the hard time limit of
        # `run_async_job`, which started before the job was cancelled.
        cancelled_before = timezone.now() - timedelta(
            seconds=settings.BASEROW_JOB_SOFT_TIME_LIMIT + 30
        )
        jobs = (
            CreateUserTemplateJob.objects.filter(
                Q(state=JOB_FAILED)
                | Q(state=JOB_CANCELLED, updated_on__lt=cancelled_before)
            )
            .exclude(template_workspace__isnull=True, archive_name="")
            # What a job that failed after its commit left is the template's.
            .exclude(template__isnull=False)
            .only("id", "template_workspace_id", "archive_name")
        )
        for job in jobs.iterator():
            # One job that can't be cleaned up must not block the others.
            try:
                self.delete_content_without_template(
                    job.template_workspace_id, job.archive_name
                )
            except Exception:
                logger.exception(
                    f"Deleting the content of create user template job {job.id} failed."
                )
                continue
            # The workspace is unset by the deletion, the archive name isn't.
            CreateUserTemplateJob.objects.filter(id=job.id).update(archive_name="")

        for content in UserTemplateContentToDelete.objects.iterator():
            self._delete_tracked_content(content)
