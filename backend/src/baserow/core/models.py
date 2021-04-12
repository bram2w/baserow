from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from rest_framework.exceptions import NotAuthenticated

from baserow.core.user_files.models import UserFile

from .managers import GroupQuerySet
from .mixins import (
    OrderableMixin,
    PolymorphicContentTypeMixin,
    CreatedAndUpdatedOnMixin,
)
from .exceptions import UserNotInGroup, UserInvalidGroupPermissionsError


__all__ = ["UserFile"]


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

    allow_new_signups = models.BooleanField(
        default=True,
        help_text="Indicates whether new users can create a new account when signing "
        "up.",
    )


class Group(CreatedAndUpdatedOnMixin, models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User, through="GroupUser")

    objects = GroupQuerySet.as_manager()

    def has_user(
        self, user, permissions=None, raise_error=False, allow_if_template=False
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
        :raises UserNotInGroup: If the user does not belong to the group.
        :raises UserInvalidGroupPermissionsError: If the user does belong to the group,
            but doesn't have the right permissions.
        :return: Indicates if the user belongs to the group.
        :rtype: bool
        """

        if permissions and not isinstance(permissions, list):
            permissions = [permissions]

        if allow_if_template and self.template_set.all().exists():
            return True
        elif not bool(user and user.is_authenticated):
            if raise_error:
                raise NotAuthenticated()
            else:
                return False

        queryset = GroupUser.objects.filter(user_id=user.id, group_id=self.id)

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


class GroupUser(CreatedAndUpdatedOnMixin, OrderableMixin, models.Model):
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


class GroupInvitation(CreatedAndUpdatedOnMixin, models.Model):
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
    CreatedAndUpdatedOnMixin, OrderableMixin, PolymorphicContentTypeMixin, models.Model
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
