from typing import Dict, NewType, Optional, Union, cast

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    Count,
    F,
    OuterRef,
    Q,
    QuerySet,
    SmallIntegerField,
    Subquery,
    Value,
)
from django.db.models.functions import Coalesce, Concat, JSONObject

from baserow_premium.license.handler import LicenseHandler

from baserow.core.models import Group
from baserow.core.trash.handler import TrashHandler
from baserow_enterprise.models import Team, TeamSubject
from baserow_enterprise.signals import (
    team_created,
    team_deleted,
    team_restored,
    team_subject_created,
    team_subject_deleted,
    team_subject_restored,
    team_updated,
)

from ..exceptions import (
    TeamDoesNotExist,
    TeamSubjectBadRequest,
    TeamSubjectDoesNotExist,
    TeamSubjectTypeUnsupported,
)
from ..features import TEAMS

TeamForUpdate = NewType("TeamForUpdate", Team)
TeamSubjectForUpdate = NewType("TeamSubjectForUpdate", TeamSubject)

SUBJECT_TYPE_USER = "auth_user"
SUPPORTED_SUBJECT_TYPES = (SUBJECT_TYPE_USER, "User")


class TeamHandler:
    def list_teams_in_group(
        self, user: AbstractUser, group: Group, subject_sample_size: int = 10
    ) -> QuerySet:
        """
        Returns a list of teams in a given group.
        """

        LicenseHandler.user_has_feature(TEAMS, user, group)

        subj_count_sq = Subquery(
            TeamSubject.objects.annotate(count=Count("id"))
            .filter(team_id=OuterRef("id"))
            .values("count"),
            output_field=SmallIntegerField(),
        )
        subj_sample_sq = (
            TeamSubject.objects.filter(team_id=OuterRef("id"))
            .annotate(
                data=JSONObject(
                    subject_id=F("subject_id"),
                    subject_type=Concat(
                        F("subject_type__app_label"),
                        Value("_"),
                        F("subject_type__model"),
                    ),
                )
            )
            .values_list("data")
            .order_by("-created_on")[:subject_sample_size]
        )
        return Team.objects.annotate(
            subject_count=Coalesce(subj_count_sq, 0),
            subject_sample=ArrayAgg(subj_sample_sq, filter=Q(subject_count__gt=0)),
        ).filter(group=group)

    def get_team(self, user: AbstractUser, team_id: int, base_queryset=None) -> Team:
        """
        Selects a team with a given id from the database.
        """

        if base_queryset is None:
            base_queryset = Team.objects

        try:
            team = base_queryset.get(id=team_id)
        except Team.DoesNotExist:
            raise TeamDoesNotExist(f"The team with id {team_id} does not exist.")

        LicenseHandler.user_has_feature(TEAMS, user, team.group)

        return team

    def get_team_for_update(self, user, team_id: int) -> TeamForUpdate:
        return cast(
            TeamForUpdate,
            self.get_team(
                user,
                team_id,
                base_queryset=Team.objects.select_for_update(of=("self",)),
            ),
        )

    def create_team(self, user: AbstractUser, name: str, group: Group) -> Team:
        """
        Creates a new team for an existing group.
        """

        LicenseHandler.user_has_feature(TEAMS, user, group)

        team = Team.objects.create(group=group, name=name)

        team_created.send(self, team_id=team.id, team=team, user=user)

        return team

    def update_team(self, user: AbstractUser, team: Team, name: str) -> Team:
        """
        Updates an existing team instance.
        """

        LicenseHandler.user_has_feature(TEAMS, user, team.group)

        team.name = name
        team.save()

        team_updated.send(self, team=team, user=user)

        return team

    def delete_team_by_id(self, user: AbstractUser, team_id: int):
        """
        Deletes a team by id, only if the user has admin permissions for the group.
        """

        locked_team = self.get_team_for_update(user, team_id)
        self.delete_team(user, locked_team)

    def delete_team(self, user: AbstractUser, team: TeamForUpdate):
        """
        Deletes an existing team if the user has admin permissions for the group.
        The team can be restored after deletion using the trash handler.
        """

        if not isinstance(team, Team):
            raise ValueError("The team is not an instance of Team.")

        LicenseHandler.user_has_feature(TEAMS, user, team.group)

        TrashHandler.trash(user, team.group, None, team)

        team_deleted.send(self, team_id=team.id, team=team, user=user)

    def restore_team_by_id(self, user: AbstractUser, team_id: int) -> Team:
        """
        Responsible for calling `restore_item` in `TrashHandler`, and once
        complete, re-fetching the newly restored `Team` so we can send a
        `team_restored` signal.
        """

        team = self.get_team(user, team_id, base_queryset=Team.objects_and_trash)
        LicenseHandler.user_has_feature(TEAMS, user, team.group)
        TrashHandler.restore_item(user, "team", team_id)
        team.refresh_from_db()
        team_restored.send(self, team_id=team.id, team=team, user=user)
        return team

    def get_teamsubject_subject_qs(self, subject, base_queryset=None) -> QuerySet:
        """ """

        if base_queryset is None:
            base_queryset = TeamSubject.objects

        return base_queryset.filter(
            subject_id=subject.id,
            subject_type=ContentType.objects.get_for_model(subject),
        )

    def get_subject(self, subject_id: int, base_queryset=None) -> TeamSubject:
        """
        Selects a subject with a given id from the database.
        """

        if base_queryset is None:
            base_queryset = TeamSubject.objects

        try:
            subject = base_queryset.get(id=subject_id)
        except TeamSubject.DoesNotExist:
            raise TeamSubjectDoesNotExist(
                f"The subject with id {subject_id} does not exist."
            )

        return subject

    def is_supported_subject_type(self, subject_natural_key: str) -> bool:
        """
        Confirms if a content type natural key is supported.
        """

        return subject_natural_key in SUPPORTED_SUBJECT_TYPES

    def create_subject(
        self,
        user: AbstractUser,
        subject_lookup: Dict[str, Union[str, int]],
        subject_natural_key: str,
        team: Team,
        pk: Optional[int] = None,
    ) -> TeamSubject:
        """
        Creates a new subject for a given team.

        If a `pk` is provided, we'll create a `TeamSubject` with an
        `id` of this value. This is used by the `TeamSubject` action
        redo to re-create a subject with the same PK.
        """

        LicenseHandler.user_has_feature(TEAMS, user, team.group)

        # Determine if this `TeamSubject` content type natural key is supported.
        if not self.is_supported_subject_type(subject_natural_key):
            raise TeamSubjectTypeUnsupported(
                f"The subject type {subject_natural_key} is unsupported."
            )

        # We only support creating a subject via an ID/PK or
        # in the case of a user, its email.
        permitted_lookups = ["id", "pk", "email"]
        unexpected_lookups = list(set(subject_lookup.keys()) - set(permitted_lookups))
        if unexpected_lookups:
            raise TeamSubjectBadRequest(
                f"A subject cannot be created with lookups {', '.join(unexpected_lookups)}."
            )

        # Split the `{app_label}_{model_label}` values, fetch the `ContentType` record.
        app_label, model_label = subject_natural_key.split("_")
        subject_ct = ContentType.objects.get(app_label=app_label, model=model_label)

        try:
            subject = subject_ct.model_class().objects.get(**subject_lookup)
        except subject_ct.model_class().DoesNotExist:
            lookup_str = ", ".join([f"{k}={v}" for k, v in subject_lookup.items()])
            raise TeamSubjectDoesNotExist(
                f"The subject with {lookup_str} and type={subject_natural_key} does not exist."
            )

        signal = team_subject_created
        create_kwargs = {"team": team, "subject": subject}
        if pk:
            create_kwargs["id"] = pk
            signal = team_subject_restored
        subject = TeamSubject.objects.create(**create_kwargs)

        signal.send(self, subject_id=subject.id, subject=subject, user=user)

        return subject

    def list_subjects_in_team(self, team_id: int) -> QuerySet:
        """
        Returns a list of subjects in a given group.
        """

        return TeamSubject.objects.filter(team=team_id)

    def get_subject_for_update(self, subject_id: int) -> TeamSubjectForUpdate:
        return cast(
            TeamSubjectForUpdate,
            self.get_subject(
                subject_id,
                base_queryset=TeamSubject.objects.select_for_update(of=("self",)),
            ),
        )

    def delete_subject_by_id(self, user: AbstractUser, subject_id: int):
        """
        Deletes a subject by id, only if the user has admin permissions
        for the group.
        """

        locked_subject = self.get_subject_for_update(subject_id)
        self.delete_subject(user, locked_subject)

    def delete_subject(self, user: AbstractUser, subject: TeamSubjectForUpdate):
        """
        Deletes an existing subject if the user has admin permissions for the group.
        The subject can be restored after deletion using the trash handler.
        """

        if not isinstance(subject, TeamSubject):
            raise ValueError("The subject is not an instance of TeamSubject.")

        LicenseHandler.user_has_feature(TEAMS, user, subject.team.group)

        subject.delete()

        team_subject_deleted.send(
            self, subject_id=subject.id, subject=subject, user=user
        )
