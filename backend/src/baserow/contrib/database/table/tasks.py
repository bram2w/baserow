from collections import defaultdict

from django.conf import settings

from baserow.config.celery import app
from baserow.contrib.database.table.object_scopes import DatabaseTableObjectScopeType
from baserow.contrib.database.table.operations import (
    ListenToAllDatabaseTableEventsOperationType,
)
from baserow.contrib.database.ws.pages import TablePageType
from baserow.core.exceptions import PermissionDenied
from baserow.core.mixins import TrashableModelMixin
from baserow.core.models import Group
from baserow.core.object_scopes import GroupObjectScopeType
from baserow.core.registries import (
    PermissionManagerType,
    object_scope_type_registry,
    subject_type_registry,
)
from baserow.core.subjects import UserSubjectType


@app.task(queue="export")
def run_row_count_job():
    """
    Runs the row count job to keep track of how many rows
    are being used by each table.
    """

    from baserow.contrib.database.table.handler import TableHandler

    TableHandler.count_rows()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    if settings.BASEROW_COUNT_ROWS_ENABLED:
        sender.add_periodic_task(
            settings.ROW_COUNT_INTERVAL,
            run_row_count_job.s(),
        )


def unsubscribe_subject_from_tables_currently_subscribed_to(
    subject_id: int,
    subject_type_name: str,
    scope_id: int,
    scope_type_name: str,
    group_id: int,
    permission_manager: PermissionManagerType = None,
):
    """
    Unsubscribes all users associated to a subject from the tables they are currently
    subscribed to. Optionally you can also recheck their permissions before deciding
    to unsubscribe them.

    :param subject_id: The id for the subject we are trying to unsubscribe
    :param subject_type_name: The name of the subject type
    :param scope_id: The id of the scope the subject should be removed from
    :param scope_type_name: The name of the scope type
    :param group_id: The id of the group in which context this is executed
    :param permission_manager: Optional parameter used to check permissions
    """

    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    group = Group.objects.get(pk=group_id)

    subject_type = subject_type_registry.get(subject_type_name)
    scope_type = object_scope_type_registry.get(scope_type_name)

    if issubclass(subject_type.model_class, TrashableModelMixin):
        subject_type_qs = subject_type.model_class.objects_and_trash
    else:
        subject_type_qs = subject_type.model_class.objects

    subject = subject_type_qs.get(pk=subject_id)
    scope = scope_type.model_class.objects.get(pk=scope_id)

    users = subject_type.get_associated_users(subject)
    tables = DatabaseTableObjectScopeType().get_all_context_objects_in_scope(scope)

    channel_group_names_users_dict = defaultdict(set)
    for user in users:
        for table in tables:
            channel_group_name = TablePageType().get_group_name(table.id)
            if permission_manager is None:
                channel_group_names_users_dict[channel_group_name].add(user.id)
            else:
                try:
                    permission_manager.check_permissions(
                        user,
                        ListenToAllDatabaseTableEventsOperationType.type,
                        group=group,
                        context=table,
                    )
                except PermissionDenied:
                    channel_group_names_users_dict[channel_group_name].add(user.id)

    channel_layer = get_channel_layer()

    for channel_group_name, user_ids in channel_group_names_users_dict.items():
        async_to_sync(channel_layer.group_send)(
            channel_group_name,
            {
                "type": "remove_user_from_group",
                "user_ids_to_remove": list(user_ids),
            },
        )


@app.task(bind=True)
def unsubscribe_user_from_table_currently_subscribed_to(
    self,
    user_id: int,
    group_id: int,
):
    """
    Unsubscribe all users associated with the subject from the table they are currently
    viewing.

    :param user_id: The id of the user that is supposed to be unsubscribed
    :param group_id: The id of the group the user belongs to
    """

    unsubscribe_subject_from_tables_currently_subscribed_to(
        user_id,
        UserSubjectType.type,
        group_id,
        GroupObjectScopeType.type,
        group_id,
    )
