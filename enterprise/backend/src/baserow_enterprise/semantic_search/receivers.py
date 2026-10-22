from django.db import transaction
from django.dispatch import receiver

from baserow.contrib.database.fields.signals import field_restored, field_updated
from baserow.core.trash.signals import before_permanently_deleted, permanently_deleted

from .handler import SemanticSearchHandler
from .models import SemanticSearchField, SemanticSearchPendingUpdate
from .tasks import delete_semantic_search_vectors

# Trashed fields and rows keep their vectors, so that they're immediately searchable
# again when restored. They're only deleted when permanently deleted.


def _delete_vectors_on_commit(table, row_ids: list[int] | None = None):
    # Rows are permanently deleted often, so the fields aren't looked up if no
    # vectors can be written. Chunks of rows that don't exist anymore are also
    # deleted by the next update of all rows.
    if row_ids is not None and not SemanticSearchHandler().is_available():
        return

    # The ids are collected now, because the `SemanticSearchField` objects are
    # deleted together with their fields.
    field_ids = list(
        SemanticSearchField.objects.filter(field__table=table).values_list(
            "field_id", flat=True
        )
    )
    if not field_ids:
        return

    if row_ids is None:
        SemanticSearchPendingUpdate.objects.filter(field_id__in=field_ids).delete()
    workspace_id = table.database.workspace_id
    transaction.on_commit(
        lambda: delete_semantic_search_vectors.delay(
            workspace_id, field_ids=field_ids, row_ids=row_ids
        )
    )


@receiver(permanently_deleted, sender="workspace")
def drop_vector_table_of_permanently_deleted_workspace(
    sender, trash_item_id, *args, **kwargs
):
    SemanticSearchHandler().drop_vector_table(trash_item_id)


@receiver(before_permanently_deleted, sender="table")
def delete_vectors_of_permanently_deleted_table(sender, trash_item, *args, **kwargs):
    _delete_vectors_on_commit(trash_item)


@receiver(before_permanently_deleted, sender="field")
def delete_vectors_of_permanently_deleted_field(sender, trash_item, *args, **kwargs):
    if not SemanticSearchField.objects.filter(field_id=trash_item.id).exists():
        return

    SemanticSearchPendingUpdate.objects.filter(field_id=trash_item.id).delete()
    workspace_id = trash_item.table.database.workspace_id
    field_id = trash_item.id
    transaction.on_commit(
        lambda: delete_semantic_search_vectors.delay(workspace_id, field_ids=[field_id])
    )


@receiver(before_permanently_deleted, sender="row")
def delete_vectors_of_permanently_deleted_row(sender, trash_item, *args, **kwargs):
    _delete_vectors_on_commit(trash_item.baserow_table, row_ids=[trash_item.id])


@receiver(before_permanently_deleted, sender="rows")
def delete_vectors_of_permanently_deleted_rows(sender, trash_item, *args, **kwargs):
    if trash_item.row_ids:
        _delete_vectors_on_commit(trash_item.table, row_ids=trash_item.row_ids)


@receiver(field_updated)
def disable_semantic_search_of_incompatible_fields(
    sender, field, related_fields, *args, **kwargs
):
    # Also the fields that changed because of another field, like a formula of
    # which the result became a number because a referenced field was converted.
    SemanticSearchHandler().disable_incompatible_fields([field, *related_fields])


@receiver(field_restored)
def queue_update_of_restored_field(sender, field, *args, **kwargs):
    # Rows created while the field was trashed haven't been indexed.
    semantic_search_field = SemanticSearchField.objects.filter(field=field).first()
    if semantic_search_field:
        SemanticSearchHandler().queue_full_updates(field.table, [semantic_search_field])
