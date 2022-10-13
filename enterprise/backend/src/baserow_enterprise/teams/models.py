from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

from baserow.core.mixins import CreatedAndUpdatedOnMixin, TrashableModelMixin
from baserow.core.models import Group


class Team(TrashableModelMixin, CreatedAndUpdatedOnMixin):
    """
    Represents a collection of `Subject` (`User`, `Team`), in a
    single group, which are grouped together under a common name.
    """

    name = models.CharField(
        max_length=160, help_text="A human friendly name for this team."
    )
    group = models.ForeignKey(
        Group,
        related_name="teams",
        on_delete=models.CASCADE,
        help_text="The group that this team belongs to.",
    )
    subjects = GenericRelation(
        "TeamSubject",
        content_type_field="subject_id",
        object_id_field="subject_type",
    )

    class Meta:
        unique_together = [["name", "group"]]
        ordering = (
            "name",
            "id",
        )

    def __str__(self) -> str:
        return f"<Team id={self.id}, name={self.name}>"


class TeamSubject(CreatedAndUpdatedOnMixin):
    """
    Represents a single `Subject` (`User`, `Team`) in a `Team`.
    """

    subject = GenericForeignKey("subject_type", "subject_id")
    subject_id = models.IntegerField(help_text="The unique subject ID.", db_index=True)
    subject_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, help_text="The subject type."
    )
    team = models.ForeignKey(
        Team,
        related_name="subjects",
        on_delete=models.CASCADE,
        help_text="The team this subject belongs to.",
    )

    def __str__(self) -> str:
        return (
            f"<TeamSubject id={self.id}, team={self.team.name}, subject={self.subject}>"
        )

    @property
    def subject_type_natural_key(self) -> str:
        """
        Responsible for returning the subject's `ContentType` natural key,
        delimited by an underscore.
        """

        return "_".join(self.subject_type.natural_key())
