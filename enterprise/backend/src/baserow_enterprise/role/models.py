import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from baserow.core.mixins import CreatedAndUpdatedOnMixin
from baserow.core.models import Group, Operation


class RoleManager(models.Manager):
    def get_by_natural_key(self, uid):
        return self.get(uid=uid)


class Role(CreatedAndUpdatedOnMixin):

    uid = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    operations = models.ManyToManyField(Operation, related_name="roles")
    default = models.BooleanField(default=False)

    group = models.ForeignKey(
        Group,
        null=True,
        related_name="roles",
        on_delete=models.CASCADE,
        help_text="The optional group that this role belongs to.",
    )

    objects = RoleManager()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"<Role '{self.name}' ({self.id})>"

    def natural_key(self):
        return (self.uid,)

    class Meta:
        ordering = ("id",)
        indexes = [
            models.Index(fields=["uid"]),
        ]


class RoleAssignment(CreatedAndUpdatedOnMixin):
    subject = GenericForeignKey("subject_type", "subject_id")
    subject_id = models.IntegerField(help_text="The unique subject ID.")
    subject_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The subject type.",
        related_name="role_subject_assignments",
    )

    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    group = models.ForeignKey(
        Group,
        related_name="role_assignments",
        on_delete=models.CASCADE,
        help_text="The group that this role assignment belongs to.",
    )

    scope = GenericForeignKey("scope_type", "scope_id")
    scope_id = models.IntegerField(help_text="The unique scope ID.")
    scope_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The scope type.",
        related_name="role_scope_assignments",
    )

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"<RoleAssignment {self.subject} - {self.role.name} - {self.group} - {self.scope}>"

    class Meta:
        ordering = ("id",)
