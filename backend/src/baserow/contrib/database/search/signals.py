from typing import TYPE_CHECKING, Type

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

from loguru import logger

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.search.handler import SearchHandler
from baserow.contrib.database.table.tasks import (
    setup_new_background_update_and_search_columns,
)
from baserow.contrib.database.tasks import (
    enqueue_task_on_commit_swallowing_any_exceptions,
)
from baserow.contrib.database.views.signals import view_loaded

if TYPE_CHECKING:
    from baserow.contrib.database.table.models import GeneratedTableModel, Table


@receiver(view_loaded)
def view_loaded_maybe_create_tsvector(
    sender,
    table: "Table",
    table_model: Type["GeneratedTableModel"],
    **kwargs,
):
    """
    Triggered when a `View` has been "loaded" (dispatched a GET
    via the API) by an API consumer. This receiver ensures that we can
    trigger some maintenance tasks when this event occurs, such as
    ensuring its corresponding table has a `tsvector` column ready for
    searching against.

    :param sender: Sender of the signal
    :param table: The Table which was accessed, directly or via a View.
    :param table_model: The GeneratedTableModel for this Table.
    :return: None
    """

    from baserow.contrib.database.search.handler import SearchHandler

    # Count the number of fields which don't yet have a `tsvector` column.
    num_fields_to_add_tsvs_for = len(table_model.get_fields_missing_search_index())

    # If we have fewer than `INITIAL_MIGRATION_FULL_TEXT_SEARCH_MAX_FIELD_LIMIT`
    # (by default: 600) fields to update, we'll try and convert the table to
    # full-text search. Anything larger than 600 will likely result in the
    # migration stalling at some point.
    if (
        num_fields_to_add_tsvs_for
        < settings.INITIAL_MIGRATION_FULL_TEXT_SEARCH_MAX_FIELD_LIMIT
    ):
        # We will migrate the table to full text search if:
        # 1. Postgres full text is enabled in our config.
        # 2. The table doesn't have its background update column.
        # 3. There are one or more fields in the table without a tsvector column.
        migrate_table_for_search = SearchHandler.full_text_enabled() and (
            not table.needs_background_update_column_added
            or num_fields_to_add_tsvs_for > 0
        )

        if migrate_table_for_search:
            logger.info(
                "Table {table_id} has {num_fields_to_add_tsvs_for} fields "
                "with no tsvector column.",
                table_id=table.id,
                num_fields_to_add_tsvs_for=num_fields_to_add_tsvs_for,
            )
            enqueue_task_on_commit_swallowing_any_exceptions(
                lambda: setup_new_background_update_and_search_columns.delay(table.id)
            )
    else:
        logger.warning(
            "Skipping turning on full text search for table {table_name}/{"
            "table_id} as it had {field_count} fields which is too many",
            table_name=table.name,
            table_id=table.id,
            field_count=num_fields_to_add_tsvs_for,
        )


@receiver(post_delete, sender=Field)
def clean_up_tsv_after_field_deleted(sender, instance, **kwargs):
    SearchHandler.after_field_perm_delete(instance)
