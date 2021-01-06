from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from baserow.core.user_files.models import UserFile

from .managers import GroupQuerySet
from .mixins import (
    OrderableMixin, PolymorphicContentTypeMixin, CreatedAndUpdatedOnMixin
)

__all__ = ['UserFile']


User = get_user_model()


def get_default_application_content_type():
    return ContentType.objects.get_for_model(Application)


class Group(CreatedAndUpdatedOnMixin, models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User, through='GroupUser')

    objects = GroupQuerySet.as_manager()

    def has_user(self, user):
        """Returns true is the user belongs to the group."""

        return self.users.filter(id=user.id).exists()

    def __str__(self):
        return f'<Group id={self.id}, name={self.name}>'


class GroupUser(CreatedAndUpdatedOnMixin, OrderableMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ('order',)

    @classmethod
    def get_last_order(cls, user):
        queryset = cls.objects.filter(user=user)
        return cls.get_highest_order_of_queryset(queryset) + 1


class Application(CreatedAndUpdatedOnMixin, OrderableMixin,
                  PolymorphicContentTypeMixin, models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField()
    content_type = models.ForeignKey(
        ContentType,
        verbose_name='content type',
        related_name='applications',
        on_delete=models.SET(get_default_application_content_type)
    )

    class Meta:
        ordering = ('order',)

    @classmethod
    def get_last_order(cls, group):
        queryset = Application.objects.filter(group=group)
        return cls.get_highest_order_of_queryset(queryset) + 1
