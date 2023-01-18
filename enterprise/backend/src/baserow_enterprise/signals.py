from django.db import transaction
from django.dispatch import Signal, receiver

from baserow.core.models import Group
from baserow.core.registries import object_scope_type_registry, subject_type_registry
from baserow.core.signals import group_user_updated
from baserow.core.types import ScopeObject, Subject
from baserow_enterprise.role.constants import (
    NO_ACCESS_ROLE_UID,
    NO_ROLE_LOW_PRIORITY_ROLE_UID,
)
from baserow_enterprise.role.models import Role
from baserow_enterprise.tasks import (
    unsubscribe_subject_from_tables_currently_subscribed_to_task,
)

team_created = Signal()
team_updated = Signal()
team_deleted = Signal()
team_restored = Signal()

team_subject_created = Signal()
team_subject_deleted = Signal()
team_subject_restored = Signal()

role_assignment_created = Signal()
role_assignment_updated = Signal()
role_assignment_deleted = Signal()


NO_ACCESS_ROLES = [NO_ACCESS_ROLE_UID, NO_ROLE_LOW_PRIORITY_ROLE_UID]


@receiver(group_user_updated)
def group_user_updated_event(sender, group_user, **kwargs):
    """
    This is triggered if a group user gets updated.
    If the updated user been assigned `NO_ACCESS` as their permission then the user will
    be unsubscribed from the table they are currently looking at, unless they have other
    permissions that grant them access.
    """

    if group_user.permissions in NO_ACCESS_ROLES:
        send_unsubscribe_subject_from_table(
            group_user.user, group_user.group, group_user.group
        )


@receiver(team_deleted)
def team_deleted_event(sender, team_id, team, user, **kwargs):
    """
    This is triggered if a team gets trashed. This means we need to kick any users
    from tables who only had access via their team.
    """

    send_unsubscribe_subject_from_table(team, team.group, team.group)


@receiver(role_assignment_updated)
@receiver(role_assignment_created)
def role_assignment_updated_event(
    sender, subject: Subject, group: Group, scope: ScopeObject, role: Role, **kwargs
):
    """
    This is triggered when a role assignment has been deleted in which case we want to
    close any subscriptions the subject might have had to a table page if the new role
    is NO_ACCESS and they therefore don't have access anymore to the scope.

    :param sender: Sender of the signal
    :param subject: Subject that has the association to the users being removed
    :param group: The group the subject is in
    :param scope: The scope the subject has been removed from
    :param role: The role the subject has been assigned
    """

    if role.uid in NO_ACCESS_ROLES:
        send_unsubscribe_subject_from_table(subject, group, scope)


@receiver(role_assignment_deleted)
def role_assignment_deleted_event(
    sender, subject: Subject, group: Group, scope: ScopeObject, **kwargs
):
    """
    This is triggered when a role assignment has been deleted in which case we want to
    close any subscriptions the subject might have had to a table page.

    :param sender: Sender of the signal
    :param subject: Subject that has the association to the users being removed
    :param group: The group the subject is in
    :param scope: The scope the subject has been removed from
    """

    send_unsubscribe_subject_from_table(subject, group, scope)


def send_unsubscribe_subject_from_table(
    subject: Subject, group: Group, scope: ScopeObject
):
    subject_id = subject.id
    subject_type_name = subject_type_registry.get_by_model(subject).type
    scope_id = scope.id
    scope_type_name = object_scope_type_registry.get_by_model(scope).type
    group_id = group.id

    transaction.on_commit(
        lambda: unsubscribe_subject_from_tables_currently_subscribed_to_task.delay(
            subject_id, subject_type_name, scope_id, scope_type_name, group_id
        )
    )
