from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property

from .managers import GroupQuerySet
from .mixins import OrderableMixin


User = get_user_model()


def get_default_application_content_type():
    return ContentType.objects.get_for_model(Application)


class Group(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User, through='GroupUser')

    objects = GroupQuerySet.as_manager()

    def has_user(self, user):
        """Returns true is the user belongs to the group."""

        return self.users.filter(id=user.id).exists()

    def __str__(self):
        return f'<Group id={self.id}, name={self.name}>'


class GroupUser(OrderableMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ('order',)

    @classmethod
    def get_last_order(cls, user):
        return cls.get_highest_order_of_queryset(cls.objects.filter(user=user)) + 1


class Application(OrderableMixin, models.Model):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.id:
            if not self.content_type_id:
                self.content_type = ContentType.objects.get_for_model(self)

    @cached_property
    def specific(self):
        """Return this page in its most specific subclassed form."""

        content_type = ContentType.objects.get_for_id(self.content_type_id)
        model_class = self.specific_class
        if model_class is None:
            return self
        elif isinstance(self, model_class):
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    @cached_property
    def specific_class(self):
        """
        Return the class that this application would be if instantiated in its
        most specific form
        """

        content_type = ContentType.objects.get_for_id(self.content_type_id)
        return content_type.model_class()

    @classmethod
    def get_last_order(cls, group):
        return cls.get_highest_order_of_queryset(
            Application.objects.filter(group=group)) + 1
