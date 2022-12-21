from baserow.config.celery import app
from baserow.contrib.database.table.tasks import (
    unsubscribe_subject_from_tables_currently_subscribed_to,
)


@app.task(bind=True)
def unsubscribe_subject_from_tables_currently_subscribed_to_task(
    self,
    subject_id: int,
    subject_type_name: str,
    scope_id: int,
    scope_type_name: str,
    group_id: int,
):
    """
    Unsubscribes a subject from a table. This can involve unsubscribing one user or
    multiple users if the subject is a Team for example.

    :param subject_id: The id for the subject we are trying to unsubscribe
    :param subject_type_name: The name of the subject type
    :param scope_id: The id of the scope the subject should be removed from
    :param scope_type_name: The name of the scope type
    :param group_id: The id of the group in which context this is executed
    """

    from baserow_enterprise.role.permission_manager import RolePermissionManagerType

    unsubscribe_subject_from_tables_currently_subscribed_to(
        subject_id,
        subject_type_name,
        scope_id,
        scope_type_name,
        group_id,
        RolePermissionManagerType(),
    )
