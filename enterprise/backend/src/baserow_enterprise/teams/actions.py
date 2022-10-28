import dataclasses
from typing import Dict, Union

from django.contrib.auth.models import AbstractUser

from baserow.core.action.models import Action
from baserow.core.action.registries import ActionScopeStr, ActionType
from baserow.core.models import Group
from baserow.core.trash.handler import TrashHandler
from baserow_enterprise.models import Team, TeamSubject
from baserow_enterprise.scopes import TeamsActionScopeType
from baserow_enterprise.teams.handler import TeamHandler


class CreateTeamActionType(ActionType):
    type = "create_team"

    @dataclasses.dataclass
    class Params:
        name: str
        team_id: int
        group_id: int

    @classmethod
    def do(cls, user: AbstractUser, name: str, group: Group) -> Team:
        """
        Creates a new team for an existing user. See
        baserow_enterprise.teams.handler.TeamHandler.create_group
        for more details. Undoing this action deletes the created team,
        redoing it restores it from the trash.

        :param user: The user creating the team.
        :param name: The name to give the team.
        :param group: The group to create the team in.
        """

        team = TeamHandler().create_team(user, name, group)

        cls.register_action(
            user=user,
            params=cls.Params(team.name, team.id, group.id),
            scope=cls.scope(team.group_id),
        )
        return team

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return TeamsActionScopeType.value(group_id)

    @classmethod
    def undo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_undo: Action,
    ):
        TeamHandler().delete_team_by_id(user, params.team_id)

    @classmethod
    def redo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_redo: Action,
    ):
        TrashHandler.restore_item(
            user, "team", params.team_id, parent_trash_item_id=None
        )


class UpdateTeamActionType(ActionType):
    type = "update_team"

    @dataclasses.dataclass
    class Params:
        team_id: int
        original_name: str
        name: str
        group_id: int

    @classmethod
    def do(cls, user: AbstractUser, team: Team, name: str) -> Team:
        """
        Updates an existing team instance.
        See baserow_enterprise.teams.handler.TeamHandler.update_team
            for further details.
        Undoing this action restore the original_name while redoing set name again.

        :param user: The user on whose behalf the team is updated.
        :param team: The team instance that needs to be updated.
        :param name: The new name of the team.
        :raises ValueError: If one of the provided parameters is invalid.
        :return: The updated team instance.
        """

        original_name = team.name

        team = TeamHandler().update_team(user, team, name)

        cls.register_action(
            user=user,
            params=cls.Params(team.id, original_name, name, team.group_id),
            scope=cls.scope(team.group_id),
        )

        return team

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return TeamsActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user: AbstractUser, params: Params, action_being_undone: Action):
        team = TeamHandler().get_team(user, params.team_id)
        TeamHandler().update_team(user, team, params.original_name)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        team = TeamHandler().get_team(user, params.team_id)
        TeamHandler().update_team(user, team, params.new_name)


class DeleteTeamActionType(ActionType):
    type = "delete_team"

    @dataclasses.dataclass
    class Params:
        team_id: int

    @classmethod
    def do(cls, user: AbstractUser, team: Team) -> None:
        """
        Deletes an existing team instance if the user has access to the
        related group. The `team_deleted` signal is also called. See
        baserow_enterprise.teams.handler.TeamHandler.delete_team for further details.
        Undoing this action restores the team and redoing trashes it.

        :param user: The user on whose behalf the team is deleted.
        :param team: The team instance that needs to be deleted.
        """

        TeamHandler().delete_team(user, team)

        cls.register_action(
            user=user,
            params=cls.Params(team.id),
            scope=cls.scope(team.group_id),
        )

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return TeamsActionScopeType.value(group_id)

    @classmethod
    def undo(cls, user, params: Params, action_being_undone: Action):
        TeamHandler().restore_team_by_id(user, params.team_id)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        team_for_update = TeamHandler().get_team_for_update(user, params.team_id)
        TeamHandler().delete_team(user, team_for_update)


class CreateTeamSubjectActionType(ActionType):
    type = "create_team_subject"

    @dataclasses.dataclass
    class Params:
        team_id: int
        subject_id: int  # TeamSubject PK
        subject_lookup: Dict[
            str, Union[str, int]
        ]  # User.email | TeamSubject.subject_id
        subject_subject_type_natural_key: int  # TeamSubject.subject_type natural key

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        subject_lookup: Dict[str, Union[str, int]],
        subject_type: str,
        team: Team,
    ) -> TeamSubject:
        """
        Creates a new subject for an existing team. See
        baserow_enterprise.teams.handler.TeamHandler.create_subject
        for more details. Undoing this action deletes the created subject,
        redoing it restores it from the trash.

        :param user: The user creating the team.
        :param subject_lookup: The subject's identifier. A dictionary pointing to
            the subject's ID/PK or an email address is required.
        :param subject_type: The subject's content type natural key.
        :param team: The team to invite the subject to.
        """

        subject = TeamHandler().create_subject(user, subject_lookup, subject_type, team)

        cls.register_action(
            user=user,
            params=cls.Params(team.id, subject.id, subject_lookup, subject_type),
            scope=cls.scope(team.group_id),
        )
        return subject

    @classmethod
    def scope(cls, group_id: int) -> ActionScopeStr:
        return TeamsActionScopeType.value(group_id)

    @classmethod
    def undo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_undo: Action,
    ):
        TeamHandler().delete_subject_by_id(user, params.subject_id)

    @classmethod
    def redo(
        cls,
        user: AbstractUser,
        params: Params,
        action_to_redo: Action,
    ):
        team = TeamHandler().get_team(user, params.team_id)
        TeamHandler().create_subject(
            user,
            params.subject_lookup,
            params.subject_subject_type_natural_key,
            team,
            params.subject_id,
        )


class DeleteTeamSubjectActionType(ActionType):
    type = "delete_team_subject"

    @dataclasses.dataclass
    class Params:
        team_id: int
        subject_id: int  # TeamSubject PK
        subject_subject_id: int  # TeamSubject.subject_id
        subject_subject_type_natural_key: int  # TeamSubject.subject_type natural key

    @classmethod
    def do(cls, user: AbstractUser, subject: TeamSubject) -> None:
        """
        Deletes an existing subject instance if the user has access to the
        related group. The `team_subject_deleted` signal is also called. See
        baserow_enterprise.teams.handler.TeamHandler.delete_team_subject for
        further details. Undoing this action restores the subject and redoing trashes it

        :param user: The user on whose behalf the team is deleted.
        :param team: The team instance that needs to be deleted.
        """

        subject_id = subject.id
        TeamHandler().delete_subject(user, subject)

        cls.register_action(
            user=user,
            params=cls.Params(
                subject.team_id,
                subject_id,
                subject.subject_id,
                subject.subject_type_natural_key,
            ),
            scope=cls.scope(subject.team.group_id),
        )

    @classmethod
    def scope(cls, team_id: int) -> ActionScopeStr:
        return TeamsActionScopeType.value(team_id)

    @classmethod
    def undo(cls, user, params: Params, action_being_undone: Action):
        team = TeamHandler().get_team(user, params.team_id)
        TeamHandler().create_subject(
            user,
            {"pk": params.subject_subject_id},
            params.subject_subject_type_natural_key,
            team,
            params.subject_id,
        )

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        TeamHandler().delete_subject_by_id(user, params.subject_id)
