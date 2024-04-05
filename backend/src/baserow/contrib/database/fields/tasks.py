import traceback
from itertools import groupby
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet

from loguru import logger
from opentelemetry import trace

from baserow.config.celery import app
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.search.handler import SearchHandler
from baserow.core.models import Workspace
from baserow.core.telemetry.utils import add_baserow_trace_attrs, baserow_trace

tracer = trace.get_tracer(__name__)


def filter_distinct_workspace_ids_per_fields(
    queryset: QuerySet, workspace_id: Optional[int] = None
) -> QuerySet:
    """
    Filters the provided queryset to only return the distinct workspace ids.

    :param queryset: The queryset that should be filtered.
    :param workspace_id: The id of the workspace that should be filtered on.
    """

    queryset = Workspace.objects.filter(
        application__database__table__field__in=queryset,
        application__trashed=False,
        application__database__table__trashed=False,
    )
    if workspace_id is not None:
        queryset = queryset.filter(id=workspace_id)
    return queryset.distinct().order_by("now")


@app.task(
    bind=True,
    queue=settings.PERIODIC_FIELD_UPDATE_QUEUE_NAME,
    soft_time_limit=settings.PERIODIC_FIELD_UPDATE_TIMEOUT_MINUTES * 60,
)
def run_periodic_fields_updates(
    self, workspace_id: Optional[int] = None, update_now: bool = True
):
    """
    Refreshes all the fields that need to be updated periodically for all
    workspaces.
    """

    for field_type_instance in field_type_registry.get_all():
        field_qs = field_type_instance.get_fields_needing_periodic_update()
        if field_qs is None:
            continue

        workspace_qs = filter_distinct_workspace_ids_per_fields(field_qs, workspace_id)

        for workspace in workspace_qs.all():
            _run_periodic_field_type_update_per_workspace(
                field_type_instance, workspace, update_now
            )


@baserow_trace(tracer)
def _run_periodic_field_type_update_per_workspace(
    field_type_instance, workspace: Workspace, update_now=True
):
    qs = field_type_instance.get_fields_needing_periodic_update()
    if qs is None:
        return

    if update_now:
        workspace.refresh_now()
    add_baserow_trace_attrs(update_now=update_now, workspace_id=workspace.id)

    all_updated_fields = []

    for field in qs.filter(
        table__database__workspace_id=workspace.id,
        table__trashed=False,
        table__database__trashed=False,
    ):
        # noinspection PyBroadException
        try:
            all_updated_fields = _run_periodic_field_update(
                field, field_type_instance, all_updated_fields
            )
        except Exception:
            tb = traceback.format_exc()
            logger.error(
                "Failed to periodically update {field_id} because of: \n{tb}",
                field_id=field.id,
                tb=tb,
            )
            continue

    # After a successful periodic update of all fields, we would need to update the
    # search index for all of them in one function per table to avoid ending up in a
    # deadlock because rows are updated simultaneously.
    for table_id, fields in groupby(all_updated_fields, lambda x: x.table_id):
        fields = list(fields)
        SearchHandler().entire_field_values_changed_or_created(fields[0].table, fields)


@baserow_trace(tracer)
def _run_periodic_field_update(field, field_type_instance, all_updated_fields):
    add_baserow_trace_attrs(field_id=field.id)
    with transaction.atomic():
        return field_type_instance.run_periodic_update(
            field, all_updated_fields=all_updated_fields
        )


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        settings.PERIODIC_FIELD_UPDATE_CRONTAB, run_periodic_fields_updates.s()
    )
