from django.db import models
from django.db.models import CASCADE, SET_NULL

import validators
from rest_framework.exceptions import ValidationError

from baserow.core.jobs.mixins import JobWithUserIpAddress
from baserow.core.jobs.models import Job
from baserow.core.mixins import (
    HierarchicalModelMixin,
    OrderableMixin,
    TrashableModelMixin,
)


def validate_domain(value: str):
    """
    Checks if the domain name follows the correct syntax.

    Note: this should exist in a validators.py, but since the module this uses is called
    "validators" we run into an importing issue where the file tries to import itself.
    Therefor this validator function is declared locally in the models.py

    :param value: The domain name that's being checked
    :raises ValidationError: If the domain name is invalid
    """

    if isinstance(validators.domain(value), validators.ValidationFailure):
        raise ValidationError("Invalid domain syntax")


class Domain(HierarchicalModelMixin, TrashableModelMixin, OrderableMixin, models.Model):
    builder = models.ForeignKey(
        "builder.Builder",
        on_delete=CASCADE,
        related_name="domains",
    )
    order = models.PositiveIntegerField()
    domain_name = models.CharField(
        max_length=255, unique=True, validators=[validate_domain]
    )
    last_published = models.DateTimeField(
        null=True,
        default=None,
        help_text="Last publication date of this domain",
    )
    published_to = models.OneToOneField(
        "builder.Builder",
        null=True,
        on_delete=SET_NULL,
        related_name="published_from",
        help_text="The published builder.",
    )

    def get_parent(self):
        return self.builder

    class Meta:
        ordering = ("order",)

    @classmethod
    def get_last_order(cls, builder):
        queryset = Domain.objects.filter(builder=builder)
        return cls.get_highest_order_of_queryset(queryset) + 1


class PublishDomainJob(JobWithUserIpAddress, Job):
    domain: Domain = models.ForeignKey(Domain, null=True, on_delete=models.SET_NULL)
