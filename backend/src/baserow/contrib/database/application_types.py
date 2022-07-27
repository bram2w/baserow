from datetime import datetime
from typing import Any, Dict, Optional, List
from zipfile import ZipFile

from django.core.files.storage import Storage
from django.core.management.color import no_style
from django.db import connection
from django.db.transaction import Atomic
from django.urls import path, include
from django.utils import timezone

from baserow.contrib.database.api.serializers import DatabaseSerializer
from baserow.contrib.database.db.schema import (
    safe_django_schema_editor,
)
from baserow.contrib.database.fields.dependencies.update_collector import (
    FieldUpdateCollector,
)
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.models import Database, Table
from baserow.contrib.database.views.registries import view_type_registry
from baserow.core.models import Application, Group
from baserow.core.registries import ApplicationType
from baserow.core.trash.handler import TrashHandler
from baserow.core.utils import ChildProgressBuilder
from baserow.core.utils import grouper
from .constants import IMPORT_SERIALIZED_IMPORTING, IMPORT_SERIALIZED_IMPORTING_TABLE
from .db.atomic import read_repeatable_single_database_atomic_transaction
from .export_serialized import DatabaseExportSerializedStructure


class DatabaseApplicationType(ApplicationType):
    type = "database"
    model_class = Database
    instance_serializer_class = DatabaseSerializer

    def pre_delete(self, database):
        """
        When a database is deleted we must also delete the related tables via the table
        handler.
        """

        database_tables = (
            database.table_set(manager="objects_and_trash")
            .all()
            .select_related("database__group")
        )

        for table in database_tables:
            TrashHandler.permanently_delete(table)

    def get_api_urls(self):
        from .api import urls as api_urls

        return [
            path("database/", include(api_urls, namespace=self.type)),
        ]

    def export_safe_transaction_context(self, application) -> Atomic:
        return read_repeatable_single_database_atomic_transaction(application.id)

    def export_tables_serialized(
        self,
        tables: List[Table],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> List[Dict[str, Any]]:
        """
        Exports the tables provided  to a serialized format that can later be
        be imported via the `import_tables_serialized`.
        """

        serialized_tables: List[Dict[str, Any]] = []
        for table in tables:
            fields = table.field_set.all()
            serialized_fields = []
            for f in fields:
                field = f.specific
                field_type = field_type_registry.get_by_model(field)
                serialized_fields.append(field_type.export_serialized(field))

            serialized_views = []
            for v in table.view_set.all():
                view = v.specific
                view_type = view_type_registry.get_by_model(view)
                serialized_views.append(
                    view_type.export_serialized(view, files_zip, storage)
                )

            model = table.get_model(fields=fields, add_dependencies=False)
            serialized_rows = []
            table_cache: Dict[str, Any] = {}
            for row in model.objects.all():
                serialized_row = DatabaseExportSerializedStructure.row(
                    id=row.id,
                    order=str(row.order),
                    created_on=row.created_on.isoformat(),
                    updated_on=row.updated_on.isoformat(),
                )
                for field_object in model._field_objects.values():
                    field_name = field_object["name"]
                    field_type = field_object["type"]
                    serialized_row[field_name] = field_type.get_export_serialized_value(
                        row, field_name, table_cache, files_zip, storage
                    )
                serialized_rows.append(serialized_row)

            serialized_tables.append(
                DatabaseExportSerializedStructure.table(
                    id=table.id,
                    name=table.name,
                    order=table.order,
                    fields=serialized_fields,
                    views=serialized_views,
                    rows=serialized_rows,
                )
            )
        return serialized_tables

    def export_serialized(
        self,
        database: Database,
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> Dict[str, Any]:
        """
        Exports the database application type to a serialized format that can later be
        be imported via the `import_serialized`.
        """

        tables = database.table_set.all().prefetch_related(
            "field_set",
            "view_set",
            "view_set__viewfilter_set",
            "view_set__viewsort_set",
        )

        serialized_tables = self.export_tables_serialized(tables, files_zip, storage)

        serialized = super().export_serialized(database, files_zip, storage)
        serialized.update(
            **DatabaseExportSerializedStructure.database(tables=serialized_tables)
        )
        return serialized

    def _ops_count_for_import_tables_serialized(
        self, serialized_tables: List[Dict[str, Any]]
    ) -> int:
        return (
            +
            # Creating each table
            len(serialized_tables)
            +
            # Creating each model table
            len(serialized_tables)
            + sum(
                [
                    # Inserting every field
                    len(table["fields"]) +
                    # Inserting every field
                    len(table["views"]) +
                    # Converting every row
                    len(table["rows"]) +
                    # Inserting every row
                    len(table["rows"]) +
                    # After each field
                    len(table["fields"])
                    for table in serialized_tables
                ]
            )
        )

    def import_tables_serialized(
        self,
        database: Database,
        serialized_tables: List[Dict[str, Any]],
        id_mapping: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> List[Table]:
        """
        Imports tables exported by the `export_tables_serialized` method.
        This method has been created in order to import single tables or partial
        applications. Beware to have all the tables needed in the
        id_mapping["database_tables"] to make this works for link-row fields.
        Look at `import_serialized` to know how to call this function.
        """

        child_total = self._ops_count_for_import_tables_serialized(serialized_tables)
        progress = ChildProgressBuilder.build(progress_builder, child_total=child_total)

        if "database_tables" not in id_mapping:
            id_mapping["database_tables"] = {}

        tables: List[Table] = []

        # First, we want to create all the table instances because it could be that
        # field or view properties depend on the existence of a table.
        for serialized_table in serialized_tables:
            table_instance = Table.objects.create(
                database=database,
                name=serialized_table["name"],
                order=serialized_table["order"],
            )
            id_mapping["database_tables"][serialized_table["id"]] = table_instance.id
            serialized_table["_object"] = table_instance
            serialized_table["_field_objects"] = []
            tables.append(table_instance)
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        # Because view properties might depend on fields, we first want to create all
        # the fields.
        fields_excluding_reversed_linked_fields = []
        none_field_count = 0
        for serialized_table in serialized_tables:
            for field in serialized_table["fields"]:
                field_type = field_type_registry.get(field["type"])
                field_instance = field_type.import_serialized(
                    serialized_table["_object"], field, id_mapping
                )

                if field_instance:
                    serialized_table["_field_objects"].append(field_instance)
                    fields_excluding_reversed_linked_fields.append(
                        (field_type, field_instance)
                    )
                else:
                    none_field_count += 1

                progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        field_cache = FieldCache()
        for field_type, field in fields_excluding_reversed_linked_fields:
            field_type.after_import_serialized(field, field_cache)

        # Now that the all tables and fields exist, we can create the views and create
        # the table schema in the database.
        for serialized_table in serialized_tables:
            for view in serialized_table["views"]:
                view_type = view_type_registry.get(view["type"])
                view_type.import_serialized(
                    serialized_table["_object"], view, id_mapping, files_zip, storage
                )
                progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

            # We don't need to create all the fields individually because the schema
            # editor can handle the creation of the table schema in one go.
            with safe_django_schema_editor() as schema_editor:
                table_model = serialized_table["_object"].get_model(
                    fields=serialized_table["_field_objects"],
                    field_ids=[],
                    managed=True,
                    add_dependencies=False,
                )
                serialized_table["_model"] = table_model
                schema_editor.create_model(table_model)

                # The auto_now_add and auto_now must be disabled for all fields
                # because the export contains correct values and we don't want them
                # to be overwritten when importing.
                for model_field in serialized_table["_model"]._meta.get_fields():
                    if hasattr(model_field, "auto_now_add"):
                        model_field.auto_now_add = False

                    if hasattr(model_field, "auto_now"):
                        model_field.auto_now = False

            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        # Now that everything is in place we can start filling the table with the rows
        # in an efficient matter by using the bulk_create functionality.
        for serialized_table in serialized_tables:
            table_model = serialized_table["_model"]
            field_ids = [
                field_object.id for field_object in serialized_table["_field_objects"]
            ]
            rows_to_be_inserted = []

            for row in serialized_table["rows"]:
                created_on = row.get("created_on")
                updated_on = row.get("updated_on")

                if created_on:
                    created_on = datetime.fromisoformat(created_on)
                else:
                    created_on = timezone.now()

                if updated_on:
                    updated_on = datetime.fromisoformat(updated_on)
                else:
                    updated_on = timezone.now()

                row_object = table_model(
                    id=row["id"],
                    order=row["order"],
                    created_on=created_on,
                    updated_on=updated_on,
                )

                for field in serialized_table["fields"]:
                    field_type = field_type_registry.get(field["type"])
                    new_field_id = id_mapping["database_fields"][field["id"]]
                    field_name = f'field_{field["id"]}'

                    # If the new field id is not present in the field_ids then we don't
                    # want to set that value on the row. This is because upon creation
                    # of the field there could be a deliberate choice not to populate
                    # that field. This is for example the case with the related field
                    # of the `link_row` field which would result in duplicates if we
                    # would populate.
                    if new_field_id in field_ids and field_name in row:
                        field_type.set_import_serialized_value(
                            row_object,
                            f'field_{id_mapping["database_fields"][field["id"]]}',
                            row[field_name],
                            id_mapping,
                            files_zip,
                            storage,
                        )

                rows_to_be_inserted.append(row_object)
                progress.increment(
                    state=f"{IMPORT_SERIALIZED_IMPORTING_TABLE}{serialized_table['id']}"
                )

            # We want to insert the rows in bulk because there could potentially be
            # hundreds of thousands of rows in there and this will result in better
            # performance.
            for chunk in grouper(512, rows_to_be_inserted):
                table_model.objects.bulk_create(chunk, batch_size=512)
                progress.increment(
                    len(chunk),
                    state=f"{IMPORT_SERIALIZED_IMPORTING_TABLE}{serialized_table['id']}",
                )

            # When the rows are inserted we keep the provide the old ids and because of
            # that the auto increment is still set at `1`. This needs to be set to the
            # maximum value because otherwise creating a new row could later fail.
            sequence_sql = connection.ops.sequence_reset_sql(no_style(), [table_model])
            with connection.cursor() as cursor:
                cursor.execute(sequence_sql[0])

        # The progress off `apply_updates_and_get_updated_fields` takes 5% of the
        # total progress of this import.
        for field_type, field in fields_excluding_reversed_linked_fields:
            update_collector = FieldUpdateCollector(field.table)
            field_type.after_rows_imported(field, update_collector, field_cache, [])
            update_collector.apply_updates_and_get_updated_fields(field_cache)
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        # Add the remaining none fields that we must not include in the import
        # because they were for example reversed link row fields.
        progress.increment(none_field_count, state=IMPORT_SERIALIZED_IMPORTING)
        return tables

    def import_serialized(
        self,
        group: Group,
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> Application:
        """
        Imports a database application exported by the `export_serialized` method.
        """

        serialized_tables = serialized_values.pop("tables")
        database_progress, table_progress = 1, 99
        progress = ChildProgressBuilder.build(
            progress_builder, child_total=database_progress + table_progress
        )

        application = super().import_serialized(
            group,
            serialized_values,
            id_mapping,
            files_zip,
            storage,
            progress.create_child_builder(represents_progress=database_progress),
        )

        database = application.specific

        if not serialized_tables:
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING, by=table_progress)
        else:
            self.import_tables_serialized(
                database,
                serialized_tables,
                id_mapping,
                files_zip,
                storage,
                progress.create_child_builder(represents_progress=table_progress),
            )

        return database
