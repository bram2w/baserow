from collections import defaultdict
from typing import List, OrderedDict

from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType

from baserow.api.user.registries import MemberDataType
from baserow_enterprise.models import TeamSubject


class EnterpriseMemberTeamsDataType(MemberDataType):
    type = "teams"

    def annotate_serialized_data(
        self, group: Group, serialized_data: List[OrderedDict]
    ) -> List[OrderedDict]:
        """
        Responsible for annotating team data on `GroupUser` responses.
        Primarily used to inform API consumers of which teams group members
        belong to.
        """

        subject_team_data = defaultdict(list)
        user_ct = ContentType.objects.get_for_model(User)
        subject_ids = [member["user_id"] for member in serialized_data]
        all_team_data = (
            TeamSubject.objects.select_related("team")
            .filter(subject_id__in=subject_ids, subject_type=user_ct)
            .values("team_id", "team__name", "subject_id")
        )
        for team_data in all_team_data:
            subject_team_data[team_data["subject_id"]].append(
                {"id": team_data["team_id"], "name": team_data["team__name"]}
            )

        for member in serialized_data:
            member[self.type] = subject_team_data.get(member["user_id"], [])

        return serialized_data
