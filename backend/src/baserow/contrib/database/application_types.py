from datetime import datetime

from django.core.management.color import no_style
from django.db import connection
from django.urls import path, include
from django.utils import timezone

from baserow.core.utils import ChildProgressBuilder
from baserow.contrib.database.api.serializers import DatabaseSerializer
from baserow.contrib.database.fields.dependencies.update_collector import (
    CachingFieldUpdateCollector,
)
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.models import Database, Table
from baserow.contrib.database.views.registries import view_type_registry
from baserow.core.registries import ApplicationType
from baserow.core.trash.handler import TrashHandler
from baserow.core.utils import grouper

from .constants import IMPORT_SERIALIZED_IMPORTING, IMPORT_SERIALIZED_IMPORTING_TABLE
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

    def export_serialized(self, database, files_zip, storage):
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
        serialized_tables = []
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
            table_cache = {}
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

        serialized = super().export_serialized(database, files_zip, storage)
        serialized.update(
            **DatabaseExportSerializedStructure.database(tables=serialized_tables)
        )
        return serialized

    def import_serialized(
        self,
        group,
        serialized_values,
        id_mapping,
        files_zip,
        storage,
        progress_builder=None,
    ):
        """
        Imports a database application exported by the `export_serialized` method.
        """

        tables = serialized_values.pop("tables")

        child_total = (
            # For the super application
            1
            +
            # Creating each table
            len(tables)
            +
            # Creating each model table
            len(tables)
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
                    for table in tables
                ]
            )
        )
        progress = ChildProgressBuilder.build(progress_builder, child_total=child_total)

        database = super().import_serialized(
            group,
            serialized_values,
            id_mapping,
            files_zip,
            storage,
            progress.create_child_builder(represents_progress=1),
        )

        if "database_tables" not in id_mapping:
            id_mapping["database_tables"] = {}

        # First, we want to create all the table instances because it could be that
        # field or view properties depend on the existence of a table.
        for table in tables:
            table_object = Table.objects.create(
                database=database,
                name=table["name"],
                order=table["order"],
            )
            id_mapping["database_tables"][table["id"]] = table_object.id
            table["_object"] = table_object
            table["_field_objects"] = []
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        # Because view properties might depend on fields, we first want to create all
        # the fields.
        all_fields = []
        none_field_count = 0
        for table in tables:
            for field in table["fields"]:
                field_type = field_type_registry.get(field["type"])
                field_object = field_type.import_serialized(
                    table["_object"], field, id_mapping
                )

                if field_object:
                    table["_field_objects"].append(field_object)
                    all_fields.append((field_type, field_object))
                else:
                    none_field_count += 1

                progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        field_cache = FieldCache()
        for field_type, field in all_fields:
            field_type.after_import_serialized(field, field_cache)

        # Now that the all tables and fields exist, we can create the views and create
        # the table schema in the database.
        for table in tables:
            for view in table["views"]:
                view_type = view_type_registry.get(view["type"])
                view_type.import_serialized(
                    table["_object"], view, id_mapping, files_zip, storage
                )
                progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

            # We don't need to create all the fields individually because the schema
            # editor can handle the creation of the table schema in one go.
            with connection.schema_editor() as schema_editor:
                model = table["_object"].get_model(
                    fields=table["_field_objects"],
                    field_ids=[],
                    managed=True,
                    add_dependencies=False,
                )
                table["_model"] = model
                schema_editor.create_model(model)

                # The auto_now_add and auto_now must be disabled for all fields
                # because the export contains correct values and we don't want them
                # to be overwritten when importing.
                for model_field in table["_model"]._meta.get_fields():
                    if hasattr(model_field, "auto_now_add"):
                        model_field.auto_now_add = False

                    if hasattr(model_field, "auto_now"):
                        model_field.auto_now = False

            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        # Now that everything is in place we can start filling the table with the rows
        # in an efficient matter by using the bulk_create functionality.
        for table in tables:
            model = table["_model"]
            field_ids = [field_object.id for field_object in table["_field_objects"]]
            rows_to_be_inserted = []

            for row in table["rows"]:
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

                row_object = model(
                    id=row["id"],
                    order=row["order"],
                    created_on=created_on,
                    updated_on=updated_on,
                )

                for field in table["fields"]:
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
                    state=f"{IMPORT_SERIALIZED_IMPORTING_TABLE}{table['id']}"
                )

            # We want to insert the rows in bulk because there could potentially be
            # hundreds of thousands of rows in there and this will result in better
            # performance.
            for chunk in grouper(512, rows_to_be_inserted):
                model.objects.bulk_create(chunk, batch_size=512)
                progress.increment(
                    len(chunk),
                    state=f"{IMPORT_SERIALIZED_IMPORTING_TABLE}{table['id']}",
                )

            # When the rows are inserted we keep the provide the old ids and because of
            # that the auto increment is still set at `1`. This needs to be set to the
            # maximum value because otherwise creating a new row could later fail.
            sequence_sql = connection.ops.sequence_reset_sql(no_style(), [model])
            with connection.cursor() as cursor:
                cursor.execute(sequence_sql[0])

        # The progress off `apply_updates_and_get_updated_fields` takes 5% of the
        # total progress of this import.
        for field_type, field in all_fields:
            update_collector = CachingFieldUpdateCollector(
                field.table, existing_field_lookup_cache=field_cache
            )
            field_type.after_rows_imported(field, [], update_collector)
            update_collector.apply_updates_and_get_updated_fields()
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        # Add the remaining none fields that we must not include in the import
        # because they were for example reversed link row fields.
        progress.increment(none_field_count, state=IMPORT_SERIALIZED_IMPORTING)

        return database
