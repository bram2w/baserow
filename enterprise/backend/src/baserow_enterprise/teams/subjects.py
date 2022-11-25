from baserow.core.models import Group
from baserow.core.registries import SubjectType
from baserow_enterprise.api.role.serializers import SubjectTeamSerializer
from baserow_enterprise.teams.models import Team


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
