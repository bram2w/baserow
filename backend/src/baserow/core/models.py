from django.db import models
from django.contrib.auth import get_user_model

from .managers import GroupQuerySet


User = get_user_model()


class Group(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User, through='GroupUser')

    objects = GroupQuerySet.as_manager()

    def has_user(self, user):
        """Returns true is the user belongs to the group."""
        return self.users.filter(id=user.id).exists()

    def __str__(self):
        return f'<Group id={self.id}, name={self.name}>'


class GroupUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ('order',)

    @classmethod
    def get_last_order(cls, user):
        """Returns a new position that will be last for a new group."""
        highest_order = cls.objects.filter(
            user=user
        ).aggregate(
            models.Max('order')
        ).get('order__max', 0) or 0

        return highest_order + 1
