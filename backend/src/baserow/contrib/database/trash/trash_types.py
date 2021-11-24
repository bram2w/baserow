from typing import Optional, Any, List

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
from baserow.core.trash.registries import TrashableItemType


class TableTrashableItemType(TrashableItemType):
    type = "table"
    model_class = Table

    def get_parent(self, trashed_item: Any, parent_id: int) -> Optional[Any]:
        return trashed_item.database

    def get_name(self, trashed_item: Table) -> str:
        return trashed_item.name

    def trashed_item_restored(self, trashed_item: Table, trash_entry: TrashEntry):
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
    def get_items_to_trash(self, trashed_item: Table) -> List[Any]:
        """
        When trashing a link row field we also want to trash the related link row field.
        """

        model = trashed_item.get_model()
        things_to_trash = [trashed_item]
        for field in model._field_objects.values():
            things_to_trash += field["type"].get_related_items_to_trash(field["field"])
        return things_to_trash


class FieldTrashableItemType(TrashableItemType):
    type = "field"
    model_class = Field

    def get_parent(self, trashed_item: Any, parent_id: int) -> Optional[Any]:
        return trashed_item.table

    def get_name(self, trashed_item: Field) -> str:
        return trashed_item.name

    def trashed_item_restored(self, trashed_item: Field, trash_entry: TrashEntry):
        FieldHandler().restore_field(trashed_item)

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
    def get_items_to_trash(self, trashed_item: Field) -> List[Any]:
        """
        When trashing a link row field we also want to trash the related link row field.
        """

        trashed_item = trashed_item.specific
        items_to_trash = [trashed_item]
        field_type = field_type_registry.get_by_model(trashed_item)
        return items_to_trash + field_type.get_related_items_to_trash(trashed_item)


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

    def trashed_item_restored(self, trashed_item, trash_entry: TrashEntry):
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
        update_collector.apply_updates_returning_updated_fields_in_start_table()
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
