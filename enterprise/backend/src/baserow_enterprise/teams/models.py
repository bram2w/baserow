from typing import Union

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

from baserow.core.mixins import CreatedAndUpdatedOnMixin, TrashableModelMixin
from baserow.core.models import Group
from baserow_enterprise.teams.mixins import ParentTeamTrashableModelMixin


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

    @property
    def default_role_uid(self) -> Union[str, None]:
        """
        Responsible for returning the team's default role `uid` for the workspace.

        If the team has been fetched with the `get_teams_queryset` queryset,
        then `_annotated_default_role_uid` will be annotated, so we can use that
        instead of querying for it.

        If we haven't used `get_teams_queryset` then we query for it.
        """

        if hasattr(self, "_annotated_default_role_uid"):
            return getattr(self, "_annotated_default_role_uid")

        from baserow_enterprise.role.handler import RoleAssignmentHandler

        role_assignment = RoleAssignmentHandler().get_current_role_assignment(
            self, self.group
        )
        if role_assignment:
            return role_assignment.role.uid


class TeamSubject(ParentTeamTrashableModelMixin, CreatedAndUpdatedOnMixin):
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

    class Meta:
        ordering = ("id",)
        indexes = [
            models.Index(
                fields=[
                    "-created_on",
                ]
            ),
        ]

    def __str__(self) -> str:
        return (
            f"<TeamSubject id={self.id}, team={self.team.name}, subject={self.subject}>"
        )

    @property
    def subject_type_natural_key(self) -> str:
        """
        Responsible for returning the subject's `ContentType`
        model class label (e.g. "auth.User").
        """

        return self.subject_type.model_class()._meta.label
