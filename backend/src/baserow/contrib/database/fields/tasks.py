import traceback
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet

from loguru import logger
from opentelemetry import trace

from baserow.config.celery import app
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.core.models import Group
from baserow.core.telemetry.utils import add_baserow_trace_attrs, baserow_trace

tracer = trace.get_tracer(__name__)


def filter_distinct_group_ids_per_fields(
    queryset: QuerySet, group_id: Optional[int] = None
) -> QuerySet:
    """
    Filters the provided queryset to only return the distinct group ids.

    :param queryset: The queryset that should be filtered.
    :param group_id: The id of the group that should be filtered on.
    """

    queryset = Group.objects.filter(application__database__table__field__in=queryset)
    if group_id is not None:
        queryset = queryset.filter(id=group_id)
    return queryset.distinct().order_by("now")


@app.task(
    bind=True,
    queue=settings.PERIODIC_FIELD_UPDATE_QUEUE_NAME,
    soft_time_limit=settings.PERIODIC_FIELD_UPDATE_TIMEOUT_MINUTES * 60,
)
def run_periodic_fields_updates(
    self, group_id: Optional[int] = None, update_now: bool = True
):
    """
    Refreshes all the fields that need to be updated periodically for all
    groups.
    """

    for field_type_instance in field_type_registry.get_all():
        field_qs = field_type_instance.get_fields_needing_periodic_update()
        if field_qs is None:
            continue

        group_qs = filter_distinct_group_ids_per_fields(field_qs, group_id)

        for group in group_qs.all():
            _run_periodic_field_type_update_per_group(
                field_type_instance, group, update_now
            )


@baserow_trace(tracer)
def _run_periodic_field_type_update_per_group(
    field_type_instance, group: Group, update_now=True
):

    qs = field_type_instance.get_fields_needing_periodic_update()
    if qs is None:
        return

    if update_now:
        group.refresh_now()
    add_baserow_trace_attrs(update_now=update_now, group_id=group.id)

    for field in qs.filter(table__database__group_id=group.id):
        # noinspection PyBroadException
        try:
            _run_periodic_field_update(field, field_type_instance)
        except Exception:
            tb = traceback.format_exc()
            logger.error(
                "Failed to periodically update {field_id} because of: \n{tb}",
                field_id=field.id,
                tb=tb,
            )
            continue


@baserow_trace(tracer)
def _run_periodic_field_update(field, field_type_instance):
    add_baserow_trace_attrs(field_id=field.id)
    with transaction.atomic():
        field_type_instance.run_periodic_update(field)


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        settings.PERIODIC_FIELD_UPDATE_CRONTAB, run_periodic_fields_updates.s()
    )
