from baserow.core.operations import GroupCoreOperationType
from baserow.core.registries import OperationType


class TeamOperationType(OperationType):
    context_scope_name = "team"


class CreateTeamOperationType(GroupCoreOperationType):
    type = "enterprise.teams.create_team"


class ReadTeamOperationType(TeamOperationType):
    type = "enterprise.teams.team.read"


class ListTeamsOperationType(GroupCoreOperationType):
    type = "enterprise.teams.list_teams"


class UpdateTeamOperationType(TeamOperationType):
    type = "enterprise.teams.team.update"


class DeleteTeamOperationType(TeamOperationType):
    type = "enterprise.teams.team.delete"


class RestoreTeamOperationType(TeamOperationType):
    type = "enterprise.teams.team.restore"


class TeamSubjectOperationType(OperationType):
    context_scope_name = "team_subject"


class CreateTeamSubjectOperationType(TeamOperationType):
    type = "enterprise.teams.create_subject"


class ReadTeamSubjectOperationType(TeamSubjectOperationType):
    type = "enterprise.teams.read_subject"


class ListTeamSubjectsOperationType(TeamOperationType):
    type = "enterprise.teams.list_subjects"


class DeleteTeamSubjectOperationType(TeamSubjectOperationType):
    type = "enterprise.teams.delete_subject"
