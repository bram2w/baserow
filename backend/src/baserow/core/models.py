import secrets
from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone as django_timezone

from baserow.core.jobs.mixins import (
    JobWithUndoRedoIds,
    JobWithUserIpAddress,
    JobWithWebsocketId,
)
from baserow.core.jobs.models import Job
from baserow.core.user_files.models import UserFile

from .action.models import Action
from .integrations.models import Integration
from .mixins import (
    CreatedAndUpdatedOnMixin,
    GroupToWorkspaceCompatModelMixin,
    HierarchicalModelMixin,
    OrderableMixin,
    ParentWorkspaceTrashableModelMixin,
    PolymorphicContentTypeMixin,
    TrashableModelMixin,
)
from .notifications.models import Notification
from .services.models import Service

__all__ = [
    "Settings",
    "Workspace",
    "WorkspaceUser",
    "WorkspaceInvitation",
    "Application",
    "TemplateCategory",
    "Template",
    "UserLogEntry",
    "TrashEntry",
    "UserFile",
    "Action",
    "Snapshot",
    "DuplicateApplicationJob",
    "InstallTemplateJob",
    "Integration",
    "Service",
    "Notification",
    "BlacklistedToken",
]


User = get_user_model()


# The difference between an admin and member right now is that an admin has
# permissions to update, delete and manage the members of a workspace.
WORKSPACE_USER_PERMISSION_ADMIN = "ADMIN"
WORKSPACE_USER_PERMISSION_MEMBER = "MEMBER"


def get_default_application_content_type():
    return ContentType.objects.get_for_model(Application)


class Operation(models.Model):
    """
    An operation
    """

    name = models.CharField(max_length=255, unique=True)


class Settings(models.Model):
    """
    The settings model represents the application wide settings that only admins can
    change. This table can only contain a single row.
    """

    instance_id = models.SlugField(default=secrets.token_urlsafe)
    allow_new_signups = models.BooleanField(
        default=True,
        help_text="Indicates whether new users can create a new account when signing "
        "up.",
    )
    allow_signups_via_workspace_invitations = models.BooleanField(
        default=True,
        help_text="Indicates whether invited users can create an account when signing "
        "up, even if allow_new_signups is disabled.",
    )
    allow_reset_password = models.BooleanField(
        default=True,
        help_text="Indicates whether users can request a password reset link.",
    )
    allow_global_workspace_creation = models.BooleanField(
        default=True,
        help_text="Indicates whether all users can create workspaces, or just staff.",
    )
    account_deletion_grace_delay = models.PositiveSmallIntegerField(
        default=30,
        help_text=(
            "Number of days after the last login for an account pending deletion "
            "to be deleted"
        ),
    )
    show_admin_signup_page = models.BooleanField(
        default=True,
        help_text="Indicates that there are no admin users in the database yet, "
        "so in the frontend the signup form will be shown instead of the login page.",
    )
    track_workspace_usage = models.BooleanField(
        default=False,
        help_text="Runs a job once per day which calculates per workspace row counts "
        "and file storage usage, displayed on the admin workspace page.",
    )


class UserProfile(models.Model):
    """
    User profile to store user specific information that can't be stored in
    default user model.
    """

    # Keep these in sync with the web-frontend options in
    # web-frontend/modules/core/enums.js
    class EmailNotificationFrequencyOptions(models.TextChoices):
        INSTANT = "instant", "instant"
        DAILY = "daily", "daily"
        WEEKLY = "weekly", "weekly"
        NEVER = "never", "never"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    language = models.TextField(
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )
    to_be_deleted = models.BooleanField(
        default=False,
        help_text="True if the user is pending deletion. "
        "An automatic task will delete the user after a grace delay.",
    )
    concurrency_limit = models.SmallIntegerField(
        null=True,
        default=None,
        blank=True,
        help_text="An optional per user concurrency limit.",
    )
    timezone = models.CharField(
        max_length=255,
        null=True,
        help_text="The user timezone to use for dates and times.",
    )
    email_notification_frequency = models.TextField(
        max_length=16,
        choices=EmailNotificationFrequencyOptions.choices,
        default=EmailNotificationFrequencyOptions.INSTANT,
    )
    last_notifications_email_sent_at = models.DateTimeField(
        null=True,
        default=None,
        help_text="The last time an email notification was sent to the user.",
    )
    # This property is used to invalidate authentication tokens that were generated
    # before this date.
    last_password_change = models.DateTimeField(
        null=True,
        default=None,
        help_text="Timestamp when the user changed their password.",
    )

    def iat_before_last_password_change(self, iat: int) -> bool:
        """
        Returns whether the iat value of a token was generated before the last
        password. This can be needed to invalidate the token if so.

        :param iat: The unix in unit timestamp format to compare with the
            `last_password_change`.
        :return: Whether the iat was before the last password change.
        """

        if not self.last_password_change:
            return False

        iat = datetime.utcfromtimestamp(iat).replace(tzinfo=timezone.utc)
        # We have to remove the milliseconds because the `iat` doesn't have
        # milliseconds in the timestamp, so that can result in the
        # `last_password_change` being higher, while it was actually done before the
        # `iat` was generated.
        last_password_change = self.last_password_change.replace(microsecond=0)
        return last_password_change > iat

    def is_jwt_token_valid(self, token):
        return not self.iat_before_last_password_change(token["iat"])


class BlacklistedToken(CreatedAndUpdatedOnMixin, models.Model):
    hashed_token = models.CharField(max_length=64, db_index=True, unique=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True
    )  # TODO delete this field in next release
    expires_at = models.DateTimeField()


class Workspace(HierarchicalModelMixin, TrashableModelMixin, CreatedAndUpdatedOnMixin):
    name = models.CharField(max_length=165)
    users = models.ManyToManyField(User, through="WorkspaceUser")
    storage_usage = models.IntegerField(null=True)
    storage_usage_updated_at = models.DateTimeField(null=True)
    seats_taken = models.IntegerField(null=True)
    seats_taken_updated_at = models.DateTimeField(null=True)
    now = models.DateTimeField(null=True)

    def get_parent(self):
        return None

    def refresh_now(self):
        self.now = django_timezone.now()
        self.save(update_fields=["now"])

    def get_now_or_set_if_null(self):
        if self.now is None:
            self.refresh_now()
        return self.now

    def application_set_including_trash(self):
        """
        :return: The applications for this workspace including any trashed applications.
        """

        return self.application_set(manager="objects_and_trash")

    def has_template(self):
        return self.template_set.all().exists()

    def get_workspace_user(
        self, user: User, include_trash: bool = False
    ) -> "WorkspaceUser":
        """
        Return the WorkspaceUser object for this workspace for the specified user.

        :param user: The user we want the workspace user for.
        :param include_trash: Do we want to check trashed workspace user also ?
        :return: The related workspace user instance.
        """

        if include_trash:
            manager = WorkspaceUser.objects_and_trash
        else:
            manager = WorkspaceUser.objects

        return manager.get(user=user, workspace=self)

    def __str__(self):
        return f"<Workspace id={self.id}, name={self.name}>"

    def __repr__(self):
        return f"<Workspace id={self.id}, name={self.name}>"


class WorkspaceUser(
    HierarchicalModelMixin,
    ParentWorkspaceTrashableModelMixin,
    GroupToWorkspaceCompatModelMixin,
    CreatedAndUpdatedOnMixin,
    OrderableMixin,
    models.Model,
):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="The user that has access to the workspace.",
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        help_text="The workspace that the user has access to.",
    )
    order = models.PositiveIntegerField(
        help_text="Unique order that the workspace has for the user."
    )
    permissions = models.CharField(
        default=WORKSPACE_USER_PERMISSION_MEMBER,
        max_length=32,
        help_text="The permissions that the user has within the workspace.",
    )

    def get_parent(self):
        return self.workspace

    class Meta:
        unique_together = [["user", "workspace"]]
        ordering = ("order",)

    @classmethod
    def get_last_order(cls, user):
        queryset = cls.objects.filter(user=user)
        return cls.get_highest_order_of_queryset(queryset) + 1


class WorkspaceInvitation(
    HierarchicalModelMixin,
    ParentWorkspaceTrashableModelMixin,
    GroupToWorkspaceCompatModelMixin,
    CreatedAndUpdatedOnMixin,
    models.Model,
):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        help_text="The workspace that the user will get access to once the invitation "
        "is accepted.",
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="The user that created the invitation.",
    )
    email = models.EmailField(
        db_index=True,
        help_text="The email address of the user that the invitation is meant for. "
        "Only a user with that email address can accept it.",
    )
    permissions = models.CharField(
        default=WORKSPACE_USER_PERMISSION_MEMBER,
        max_length=32,
        help_text="The permissions that the user is going to get within the workspace "
        "after accepting the invitation.",
    )
    message = models.TextField(
        blank=True,
        max_length=250,
        help_text="An optional message that the invitor can provide. This will be "
        "visible to the receiver of the invitation.",
    )

    def get_parent(self):
        return self.workspace

    class Meta:
        ordering = ("id",)


class Application(
    HierarchicalModelMixin,
    TrashableModelMixin,
    CreatedAndUpdatedOnMixin,
    OrderableMixin,
    PolymorphicContentTypeMixin,
    GroupToWorkspaceCompatModelMixin,
    models.Model,
):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=160)
    order = models.PositiveIntegerField()
    content_type = models.ForeignKey(
        ContentType,
        verbose_name="content type",
        related_name="applications",
        on_delete=models.SET(get_default_application_content_type),
    )
    installed_from_template = models.ForeignKey(
        "Template",
        on_delete=models.SET_NULL,
        null=True,
        related_name="installed_applications",
    )

    class Meta:
        ordering = ("order",)

    @classmethod
    def get_last_order(cls, workspace):
        queryset = Application.objects.filter(workspace=workspace)
        return cls.get_highest_order_of_queryset(queryset) + 1

    def get_parent(self):
        # If this application is an application snapshot, then it'll
        # have a None workspace, so instead we define its parent as
        # the source snapshot's `snapshot_from`.
        if self.workspace_id:
            return self.workspace
        else:
            return self.snapshot_from.get()


class TemplateCategory(models.Model):
    name = models.CharField(max_length=32)

    class Meta:
        ordering = ("name",)


class Template(GroupToWorkspaceCompatModelMixin, models.Model):
    name = models.CharField(max_length=64)
    slug = models.SlugField(
        help_text="The template slug that is used to match the template with the JSON "
        "file name."
    )
    icon = models.CharField(
        max_length=32,
        help_text="The icon class name that can be used for displaying purposes.",
    )
    categories = models.ManyToManyField(TemplateCategory, related_name="templates")
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The group containing the applications related to the template. The "
        "read endpoints related to that group are publicly accessible for "
        "preview purposes.",
    )
    export_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="The export hash that is used to compare if the exported group "
        "applications have changed when syncing the templates.",
    )
    keywords = models.TextField(
        default="",
        blank=True,
        help_text="Keywords related to the template that can be used for search.",
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class UserLogEntry(models.Model):
    actor = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=(("SIGNED_IN", "Signed in"),))
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = "timestamp"
        ordering = ["-timestamp"]


class TrashEntry(GroupToWorkspaceCompatModelMixin, models.Model):
    """
    A TrashEntry is a record indicating that another model in Baserow has a trashed
    row. When a user deletes certain things in Baserow they are not actually deleted
    from the database, but instead marked as trashed. Trashed rows can be restored
    or permanently deleted.

    The other model must mixin the TrashableModelMixin and also have a corresponding
    TrashableItemType registered specifying exactly how to delete and restore that
    model.
    """

    # The TrashableItemType.type of the item that is trashed.
    trash_item_type = models.TextField()
    # We need to also store the parent id as for some trashable items the
    # trash_item_type and the trash_item_id is not unique as the items of that type
    # could be spread over multiple tables with the same id.
    parent_trash_item_id = models.PositiveIntegerField(null=True, blank=True)
    # The actual id of the item that is trashed
    trash_item_id = models.PositiveIntegerField()

    trash_item_owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="private_trash_entries",
    )

    # If the user who trashed something gets deleted we still wish to preserve this
    # trash record as it is independent of if the user exists or not.
    user_who_trashed = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    # The workspace and application fields are used to workspace trash into
    # separate "bins" which can be viewed and emptied independently of each other.

    # The workspace the item that is trashed is found in, if the trashed item is the
    # workspace itself then this should also be set to that trashed workspace.
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    # The application the item that is trashed is found in, if the trashed item is the
    # application itself then this should also be set to that trashed application.
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, null=True, blank=True
    )

    # When set to true this trash entry will be picked up by a periodic job and the
    # underlying item will be actually permanently deleted along with the entry.
    should_be_permanently_deleted = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(auto_now_add=True)

    # The name, name of the parent and any extra description are cached so lookups
    # of trashed items are simple and do not require joining to many different tables
    # to simply get these details.
    name = models.TextField()
    # If multiple items have been deleted via one trash entry, for example with a
    # batch update, the names can be provided here. The client can then visualize
    # this differently.
    names = ArrayField(base_field=models.TextField(), null=True)
    parent_name = models.TextField(null=True, blank=True)
    extra_description = models.TextField(null=True, blank=True)

    # this permits to trash items together with a single entry
    related_items = models.JSONField(default=dict, null=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["trash_item_type", "parent_trash_item_id", "trash_item_id"],
                name="unique_with_parent_trash_item_id",
            ),
            UniqueConstraint(
                fields=["trash_item_type", "trash_item_id"],
                condition=Q(parent_trash_item_id=None),
                name="unique_without_parent_trash_item_id",
            ),
        ]
        indexes = [
            models.Index(
                fields=["-trashed_at", "trash_item_type", "workspace", "application"]
            )
        ]


class DuplicateApplicationJob(
    JobWithUserIpAddress, JobWithWebsocketId, JobWithUndoRedoIds, Job
):
    original_application = models.ForeignKey(
        Application,
        null=True,
        related_name="duplicated_by_jobs",
        on_delete=models.SET_NULL,
        help_text="The Baserow application to duplicate.",
    )
    duplicated_application = models.OneToOneField(
        Application,
        null=True,
        related_name="duplicated_from_jobs",
        on_delete=models.SET_NULL,
        help_text="The duplicated Baserow application.",
    )


class Snapshot(HierarchicalModelMixin, models.Model):
    name = models.CharField(max_length=160)
    snapshot_from_application = models.ForeignKey(
        Application, on_delete=models.CASCADE, null=False, related_name="snapshot_to"
    )
    snapshot_to_application = models.ForeignKey(
        Application, on_delete=models.CASCADE, null=True, related_name="snapshot_from"
    )
    mark_for_deletion = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("name", "snapshot_from_application")

    def get_parent(self):
        return self.snapshot_from_application


class InstallTemplateJob(
    GroupToWorkspaceCompatModelMixin,
    JobWithUserIpAddress,
    JobWithWebsocketId,
    JobWithUndoRedoIds,
    Job,
):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        help_text="The group where the template is installed.",
    )
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        help_text="The template that is installed.",
    )
    installed_applications = models.JSONField(default=list)
