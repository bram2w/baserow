from typing import List

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType

from baserow.core.models import Group
from baserow.core.registries import SubjectType
from baserow_enterprise.api.role.serializers import SubjectTeamSerializer
from baserow_enterprise.teams.models import Team, TeamSubject

User = get_user_model()


class TeamSubjectType(SubjectType):
    type = "baserow_enterprise.Team"
    model_class = Team

    def is_in_group(self, subject_id: int, group: Group) -> bool:
        return Team.objects.filter(
            id=subject_id,
            group=group,
            trashed=False,
        ).exists()

    def get_serializer(self, model_instance, **kwargs):
        return SubjectTeamSerializer(model_instance, **kwargs)

    def get_associated_users(self, team: Team) -> List[AbstractUser]:
        return list(
            User.objects.filter(
                pk__in=TeamSubject.objects_and_trash.filter(
                    team_id=team.id,
                    subject_type=ContentType.objects.get_for_model(User),
                ).values_list("subject_id", flat=True)
            )
        )
