import secrets

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import UniqueConstraint, Q

from rest_framework.exceptions import NotAuthenticated

from baserow.core.user_files.models import UserFile

from .mixins import (
    OrderableMixin,
    PolymorphicContentTypeMixin,
    CreatedAndUpdatedOnMixin,
    TrashableModelMixin,
    ParentGroupTrashableModelMixin,
)
from .exceptions import UserNotInGroup, UserInvalidGroupPermissionsError


__all__ = [
    "Settings",
    "Group",
    "GroupUser",
    "GroupInvitation",
    "Application",
    "TemplateCategory",
    "Template",
    "UserLogEntry",
    "TrashEntry",
    "UserFile",
]


User = get_user_model()


# The difference between an admin and member right now is that an admin has
# permissions to update, delete and manage the members of a group.
GROUP_USER_PERMISSION_ADMIN = "ADMIN"
GROUP_USER_PERMISSION_MEMBER = "MEMBER"
GROUP_USER_PERMISSION_CHOICES = (
    (GROUP_USER_PERMISSION_ADMIN, "Admin"),
    (GROUP_USER_PERMISSION_MEMBER, "Member"),
)


def get_default_application_content_type():
    return ContentType.objects.get_for_model(Application)


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


class UserProfile(models.Model):
    """
    User profile to store user specific information that can't be stored in
    default user model.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    language = models.TextField(
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )


class Group(TrashableModelMixin, CreatedAndUpdatedOnMixin):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User, through="GroupUser")

    def application_set_including_trash(self):
        """
        :return: The applications for this group including any trashed applications.
        """
        return self.application_set(manager="objects_and_trash")

    def has_template(self):
        return self.template_set.all().exists()

    def has_user(
        self,
        user,
        permissions=None,
        raise_error=False,
        allow_if_template=False,
        include_trash=False,
    ):
        """
        Checks if the provided user belongs to the group.

        :param user: The user that must be in the group.
        :type user: User
        :param permissions: One or multiple permissions can optionally be provided
            and if so, the user must have one of those permissions.
        :type permissions: None, str or list
        :param raise_error: If True an error will be raised when the user does not
            belong to the group or doesn't have the right permissions.
        :type raise_error: bool
        :param allow_if_template: If true and if the group is related to a template,
            then True is always returned and no exception will be raised.
        :type allow_if_template: bool
        :param include_trash: If true then also checks if the group has been trashed
            instead of raising a DoesNotExist exception.
        :type include_trash: bool
        :raises UserNotInGroup: If the user does not belong to the group.
        :raises UserInvalidGroupPermissionsError: If the user does belong to the group,
            but doesn't have the right permissions.
        :return: Indicates if the user belongs to the group.
        :rtype: bool
        """

        if permissions and not isinstance(permissions, list):
            permissions = [permissions]

        if allow_if_template and self.has_template():
            return True
        elif not bool(user and user.is_authenticated):
            if raise_error:
                raise NotAuthenticated()
            else:
                return False

        if include_trash:
            manager = GroupUser.objects_and_trash
        else:
            manager = GroupUser.objects

        queryset = manager.filter(user_id=user.id, group_id=self.id)

        if raise_error:
            try:
                group_user = queryset.get()
            except GroupUser.DoesNotExist:
                raise UserNotInGroup(user, self)

            if permissions is not None and group_user.permissions not in permissions:
                raise UserInvalidGroupPermissionsError(user, self, permissions)
        else:
            if permissions is not None:
                queryset = queryset.filter(permissions__in=permissions)

            return queryset.exists()

    def __str__(self):
        return f"<Group id={self.id}, name={self.name}>"


class GroupUser(
    ParentGroupTrashableModelMixin,
    CreatedAndUpdatedOnMixin,
    OrderableMixin,
    models.Model,
):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="The user that has access to the group.",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        help_text="The group that the user has access to.",
    )
    order = models.PositiveIntegerField(
        help_text="Unique order that the group has for the user."
    )
    permissions = models.CharField(
        default=GROUP_USER_PERMISSION_MEMBER,
        max_length=32,
        choices=GROUP_USER_PERMISSION_CHOICES,
        help_text="The permissions that the user has within the group.",
    )

    class Meta:
        unique_together = [["user", "group"]]
        ordering = ("order",)

    @classmethod
    def get_last_order(cls, user):
        queryset = cls.objects.filter(user=user)
        return cls.get_highest_order_of_queryset(queryset) + 1


class GroupInvitation(
    ParentGroupTrashableModelMixin, CreatedAndUpdatedOnMixin, models.Model
):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        help_text="The group that the user will get access to once the invitation is "
        "accepted.",
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
        default=GROUP_USER_PERMISSION_MEMBER,
        max_length=32,
        choices=GROUP_USER_PERMISSION_CHOICES,
        help_text="The permissions that the user is going to get within the group "
        "after accepting the invitation.",
    )
    message = models.TextField(
        blank=True,
        help_text="An optional message that the invitor can provide. This will be "
        "visible to the receiver of the invitation.",
    )

    class Meta:
        ordering = ("id",)


class Application(
    TrashableModelMixin,
    CreatedAndUpdatedOnMixin,
    OrderableMixin,
    PolymorphicContentTypeMixin,
    models.Model,
):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField()
    content_type = models.ForeignKey(
        ContentType,
        verbose_name="content type",
        related_name="applications",
        on_delete=models.SET(get_default_application_content_type),
    )

    class Meta:
        ordering = ("order",)

    @classmethod
    def get_last_order(cls, group):
        queryset = Application.objects.filter(group=group)
        return cls.get_highest_order_of_queryset(queryset) + 1


class TemplateCategory(models.Model):
    name = models.CharField(max_length=32)

    class Meta:
        ordering = ("name",)


class Template(models.Model):
    name = models.CharField(max_length=64)
    slug = models.SlugField(
        help_text="The template slug that is used to match the template with the JSON "
        "file name."
    )
    icon = models.CharField(
        max_length=32,
        help_text="The font awesome class name that can be used for displaying "
        "purposes.",
    )
    categories = models.ManyToManyField(TemplateCategory, related_name="templates")
    group = models.ForeignKey(
        Group,
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


class UserLogEntry(models.Model):
    actor = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=(("SIGNED_IN", "Signed in"),))
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = "timestamp"
        ordering = ["-timestamp"]


class TrashEntry(models.Model):
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

    # If the user who trashed something gets deleted we still wish to preserve this
    # trash record as it is independent of if the user exists or not.
    user_who_trashed = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    # The group and application fields are used to group trash into separate "bins"
    # which can be viewed and emptied independently of each other.

    # The group the item that is trashed is found in, if the trashed item is the
    # group itself then this should also be set to that trashed group.
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
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
    parent_name = models.TextField(null=True, blank=True)
    extra_description = models.TextField(null=True, blank=True)

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
                fields=["-trashed_at", "trash_item_type", "group", "application"]
            )
        ]
