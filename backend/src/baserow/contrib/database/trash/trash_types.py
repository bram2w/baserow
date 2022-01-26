from typing import Optional, Any

from django.contrib.auth import get_user_model
from django.db import connection

from baserow.contrib.database.fields.dependencies.update_collector import (
    CachingFieldUpdateCollector,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.signals import row_created
from baserow.contrib.database.table.models import Table, GeneratedTableModel
from baserow.contrib.database.table.signals import table_created
from baserow.core.exceptions import TrashItemDoesNotExist
from baserow.core.models import TrashEntry
from baserow.core.trash.exceptions import RelatedTableTrashedException
from baserow.core.trash.registries import TrashableItemType

User = get_user_model()


class TableTrashableItemType(TrashableItemType):
    type = "table"
    model_class = Table

    def get_parent(self, trashed_item: Any, parent_id: int) -> Optional[Any]:
        return trashed_item.database

    def get_name(self, trashed_item: Table) -> str:
        return trashed_item.name

    def restore(self, trashed_item: Table, trash_entry: TrashEntry):
        super().restore(trashed_item, trash_entry)

        update_collector = CachingFieldUpdateCollector(trashed_item)
        field_handler = FieldHandler()
        for field in trashed_item.field_set(manager="objects_and_trash").all():
            field = field.specific
            field_type = field_type_registry.get_by_model(field)
            field_ids_to_check_for_individual_entries = [field.id] + [
                f.id
                for f in field_type.get_other_fields_to_trash_restore_always_together(
                    field
                )
            ]
            if TrashEntry.objects.filter(
                trash_item_type="field",
                trash_item_id__in=field_ids_to_check_for_individual_entries,
                application=trashed_item.database,
                group=trashed_item.database.group,
            ).exists():
                # Don't restore fields with their own trash entry as they have been
                # separately deleted individually before the table was deleted.
                continue

            try:
                field_handler.restore_field(
                    field,
                    apply_and_send_updates=False,
                    update_collector=update_collector,
                )
            except RelatedTableTrashedException:
                continue

            update_collector.cache_field(field)
        update_collector.apply_updates_and_get_updated_fields()
        update_collector.send_additional_field_updated_signals()

        table_created.send(
            self,
            table=trashed_item,
            user=None,
        )

    def permanently_delete_item(
        self,
        trashed_item: Table,
        trash_item_lookup_cache=None,
    ):
        """Deletes the table schema and instance."""

        if (
            trash_item_lookup_cache is not None
            and "row_table_model_cache" in trash_item_lookup_cache
        ):
            # Invalidate the cached model for this table after it is deleted as
            # otherwise a row being deleted after will use the cached model and assume
            # it still exists.
            trash_item_lookup_cache["row_table_model_cache"].pop(trashed_item.id, None)

        with connection.schema_editor() as schema_editor:
            model = trashed_item.get_model()
            schema_editor.delete_model(model)

        trashed_item.delete()

    # noinspection PyMethodMayBeStatic
    def trash(self, item_to_trash: Table, requesting_user: User):
        model = item_to_trash.get_model()

        update_collector = CachingFieldUpdateCollector(item_to_trash)
        handler = FieldHandler()

        for field in model._field_objects.values():
            field = field["field"]
            # One of the previously deleted fields might have cached this field we
            # now want to delete, ensure it is gone from the cache as presence in the
            # cache is treated as the field not being trashed in other code.
            update_collector.uncache_field(field)
            handler.delete_field(
                requesting_user,
                field,
                create_separate_trash_entry=False,
                apply_and_send_updates=False,
                update_collector=update_collector,
                allow_deleting_primary=True,
            )

        update_collector.apply_updates_and_get_updated_fields()
        update_collector.send_additional_field_updated_signals()

        super().trash(item_to_trash, requesting_user)


class FieldTrashableItemType(TrashableItemType):
    type = "field"
    model_class = Field

    def get_parent(self, trashed_item: Any, parent_id: int) -> Optional[Any]:
        return trashed_item.table

    def get_name(self, trashed_item: Field) -> str:
        return trashed_item.name

    def restore(self, trashed_item: Field, trash_entry: TrashEntry):
        FieldHandler().restore_field(trashed_item.specific)

    def permanently_delete_item(
        self,
        field: Field,
        trash_item_lookup_cache=None,
    ):
        """Deletes the table schema and instance."""

        if (
            trash_item_lookup_cache is not None
            and "row_table_model_cache" in trash_item_lookup_cache
        ):
            # Invalidate the cached model for this field's table as after this field is
            # deleted usage of the old model will cause ProgrammingError's as the column
            # for this field no longer exists.
            trash_item_lookup_cache["row_table_model_cache"].pop(field.table.id, None)

        field = field.specific
        field_type = field_type_registry.get_by_model(field)

        # Remove the field from the table schema.
        with connection.schema_editor() as schema_editor:
            from_model = field.table.get_model(field_ids=[], fields=[field])
            model_field = from_model._meta.get_field(field.db_column)
            schema_editor.remove_field(from_model, model_field)

        field.delete()

        # After the field is deleted we are going to to call the after_delete method of
        # the field type because some instance cleanup might need to happen.
        field_type.after_delete(field, from_model, connection)

    # noinspection PyMethodMayBeStatic
    def trash(self, item_to_trash: Field, requesting_user: User):
        """
        When trashing a link row field we also want to trash the related link row field.
        """

        item_to_trash = item_to_trash.specific
        super().trash(item_to_trash, requesting_user)

        field_type = field_type_registry.get_by_model(item_to_trash)
        for (
            related_field
        ) in field_type.get_other_fields_to_trash_restore_always_together(
            item_to_trash
        ):
            if not related_field.trashed:
                FieldHandler().delete_field(
                    requesting_user, related_field, create_separate_trash_entry=False
                )


class RowTrashableItemType(TrashableItemType):
    type = "row"
    model_class = GeneratedTableModel

    @property
    def requires_parent_id(self) -> bool:
        # A row is not unique just with its ID. We also need the table id (parent id)
        # to uniquely identify and lookup a specific row.
        return True

    def get_parent(self, trashed_item: Any, parent_id: int) -> Optional[Any]:
        return self._get_table(parent_id)

    @staticmethod
    def _get_table(parent_id):
        try:
            return Table.objects_and_trash.get(id=parent_id)
        except Table.DoesNotExist:
            # The parent table must have been actually deleted, in which case the
            # row itself no longer exits.
            raise TrashItemDoesNotExist()

    def get_name(self, trashed_item) -> str:
        return str(trashed_item.id)

    def restore(self, trashed_item, trash_entry: TrashEntry):
        super().restore(trashed_item, trash_entry)

        table = self.get_parent(trashed_item, trash_entry.parent_trash_item_id)

        model = table.get_model()

        update_collector = CachingFieldUpdateCollector(
            table, existing_model=model, starting_row_id=trashed_item.id
        )
        updated_fields = [f["field"] for f in model._field_objects.values()]
        for field in updated_fields:
            for (
                dependant_field,
                dependant_field_type,
                path_to_starting_table,
            ) in field.dependant_fields_with_types(update_collector):
                dependant_field_type.row_of_dependency_created(
                    dependant_field,
                    trashed_item,
                    update_collector,
                    path_to_starting_table,
                )
        update_collector.apply_updates_and_get_updated_fields()
        row_created.send(
            self,
            row=trashed_item,
            table=table,
            model=model,
            before=None,
            user=None,
        )

    def permanently_delete_item(self, row, trash_item_lookup_cache=None):
        row.delete()

    def lookup_trashed_item(
        self, trashed_entry: TrashEntry, trash_item_lookup_cache=None
    ):
        """
        Returns the actual instance of the trashed item. By default simply does a get
        on the model_class's trash manager.

        :param trash_item_lookup_cache: A cache dict used to store the generated models
            for a given table so if looking up many rows from the same table we only
            need to lookup the tables fields etc once.
        :param trashed_entry: The entry to get the real trashed instance for.
        :return: An instance of the model_class with trashed_item_id
        """

        # Cache the expensive table.get_model function call if we are looking up
        # many trash items at once.
        if trash_item_lookup_cache is not None:
            model_cache = trash_item_lookup_cache.setdefault(
                "row_table_model_cache", {}
            )
            try:
                model = model_cache[trashed_entry.parent_trash_item_id]
            except KeyError:
                model = model_cache.setdefault(
                    trashed_entry.parent_trash_item_id,
                    self._get_table_model(trashed_entry.parent_trash_item_id),
                )
        else:
            model = self._get_table_model(trashed_entry.parent_trash_item_id)

        try:
            return model.trash.get(id=trashed_entry.trash_item_id)
        except model.DoesNotExist:
            raise TrashItemDoesNotExist()

    def _get_table_model(self, table_id):
        table = self._get_table(table_id)
        return table.get_model()

    # noinspection PyMethodMayBeStatic
    def get_extra_description(self, trashed_item: Any, table) -> Optional[str]:

        model = table.get_model()
        for field in model._field_objects.values():
            if field["field"].primary:
                primary_value = field["type"].get_human_readable_value(
                    getattr(trashed_item, field["name"]), field
                )
                if primary_value is None or primary_value == "":
                    primary_value = f"unnamed row {trashed_item.id}"
                return primary_value

        return "unknown row"
