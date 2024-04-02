import traceback
from itertools import groupby
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet

from loguru import logger
from opentelemetry import trace

from baserow.config.celery import app
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import AIField
from baserow.contrib.database.fields.operations import ListFieldsOperationType
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.exceptions import RowDoesNotExist
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.runtime_formula_contexts import (
    HumanReadableRowContext,
)
from baserow.contrib.database.rows.signals import rows_ai_values_generation_error
from baserow.contrib.database.search.handler import SearchHandler
from baserow.core.formula import resolve_formula
from baserow.core.formula.registries import formula_runtime_function_registry
from baserow.core.generative_ai.exceptions import ModelDoesNotBelongToType
from baserow.core.generative_ai.registries import generative_ai_model_type_registry
from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace
from baserow.core.telemetry.utils import add_baserow_trace_attrs, baserow_trace
from baserow.core.user.handler import User

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


@app.task(bind=True, queue="export")
def generate_ai_values_for_rows(self, user_id: int, field_id: int, row_ids: list[int]):
    user = User.objects.get(pk=user_id)

    ai_field = FieldHandler().get_field(
        field_id,
        base_queryset=AIField.objects.all().select_related(
            "table__database__workspace"
        ),
    )
    table = ai_field.table

    CoreHandler().check_permissions(
        user,
        ListFieldsOperationType.type,
        workspace=table.database.workspace,
        context=table,
    )

    model = ai_field.table.get_model()
    req_row_ids = row_ids
    rows = RowHandler().get_rows(model, req_row_ids)
    if len(rows) != len(req_row_ids):
        found_rows_ids = [row.id for row in rows]
        raise RowDoesNotExist(sorted(list(set(req_row_ids) - set(found_rows_ids))))

    generative_ai_model_type = generative_ai_model_type_registry.get(
        ai_field.ai_generative_ai_type
    )
    ai_models = generative_ai_model_type.get_enabled_models()

    if ai_field.ai_generative_ai_model not in ai_models:
        raise ModelDoesNotBelongToType(model_name=ai_field.ai_generative_ai_model)

    for i, row in enumerate(rows):
        context = HumanReadableRowContext(row, exclude_field_ids=[ai_field.id])
        message = str(
            resolve_formula(
                ai_field.ai_prompt, formula_runtime_function_registry, context
            )
        )

        try:
            value = generative_ai_model_type.prompt(
                ai_field.ai_generative_ai_model, message
            )
        except Exception as exc:
            # If the prompt fails once, we should not continue with the other rows.
            rows_ai_values_generation_error.send(
                self,
                user=user,
                rows=rows[i:],
                field=ai_field,
                table=table,
                error_message=str(exc),
            )
            raise exc

        RowHandler().update_row_by_id(
            user,
            table,
            row.id,
            {ai_field.db_column: value},
            model=model,
            values_already_prepared=True,
        )


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
