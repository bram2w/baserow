from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from zipfile import ZipFile

from django.core.files.storage import Storage
from django.core.management.color import no_style
from django.db import connection, models
from django.db.models import Prefetch
from django.db.transaction import Atomic
from django.urls import include, path
from django.utils import timezone, translation
from django.utils.translation import gettext as _

from baserow.contrib.database.api.serializers import DatabaseSerializer
from baserow.contrib.database.db.schema import safe_django_schema_editor
from baserow.contrib.database.fields.dependencies.handler import FieldDependencyHandler
from baserow.contrib.database.fields.dependencies.update_collector import (
    FieldUpdateCollector,
)
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.models import Database, Field, View
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.views.registries import view_type_registry
from baserow.core.db import specific_queryset
from baserow.core.handler import CoreHandler
from baserow.core.models import Application, Workspace
from baserow.core.registries import (
    ApplicationType,
    ImportExportConfig,
    serialization_processor_registry,
)
from baserow.core.trash.handler import TrashHandler
from baserow.core.utils import ChildProgressBuilder, grouper

from .constants import IMPORT_SERIALIZED_IMPORTING, IMPORT_SERIALIZED_IMPORTING_TABLE
from .db.atomic import read_repeatable_single_database_atomic_transaction
from .export_serialized import DatabaseExportSerializedStructure
from .fields.deferred_field_fk_updater import DeferredFieldFkUpdater
from .search.handler import SearchHandler
from .table.models import Table


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
            .select_related("database__workspace")
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
        import_export_config: ImportExportConfig,
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

            table_cache: Dict[str, Any] = {}
            workspace = table.get_root()
            if workspace is not None:
                table_cache["workspace_id"] = workspace.id
            serialized_views = []
            for v in table.view_set.all():
                view = v.specific
                view_type = view_type_registry.get_by_model(view)
                serialized_views.append(
                    view_type.export_serialized(view, table_cache, files_zip, storage)
                )

            model = table.get_model(fields=fields, add_dependencies=False)
            serialized_rows = []
            row_queryset = model.objects.all()
            if table.last_modified_by_column_added:
                row_queryset = row_queryset.select_related("last_modified_by")
            for row in row_queryset:
                serialized_row = DatabaseExportSerializedStructure.row(
                    id=row.id,
                    order=str(row.order),
                    created_on=row.created_on.isoformat(),
                    updated_on=row.updated_on.isoformat(),
                    last_modified_by=getattr(row, "last_modified_by", None),
                )
                for field_object in model._field_objects.values():
                    field_name = field_object["name"]
                    field_type = field_object["type"]
                    serialized_row[field_name] = field_type.get_export_serialized_value(
                        row, field_name, table_cache, files_zip, storage
                    )
                serialized_rows.append(serialized_row)

            structure = DatabaseExportSerializedStructure.table(
                id=table.id,
                name=table.name,
                order=table.order,
                fields=serialized_fields,
                views=serialized_views,
                rows=serialized_rows,
            )

            for serialized_structure in serialization_processor_registry.get_all():
                extra_data = serialized_structure.export_serialized(
                    workspace, table, import_export_config
                )
                if extra_data is not None:
                    structure.update(**extra_data)
            serialized_tables.append(structure)
        return serialized_tables

    def export_serialized(
        self,
        database: Database,
        import_export_config: ImportExportConfig,
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> Dict[str, Any]:
        """
        Exports the database application type to a serialized format that can later
        be imported via the `import_serialized`.
        """

        tables = database.table_set.all().prefetch_related(
            Prefetch("field_set", queryset=specific_queryset(Field.objects.all())),
            "field_set__select_options",
            Prefetch(
                "view_set",
                queryset=specific_queryset(
                    View.objects.all().select_related("owned_by")
                ),
            ),
            "view_set__viewfilter_set",
            "view_set__filter_groups",
            "view_set__viewsort_set",
            "view_set__viewgroupby_set",
            "view_set__viewdecoration_set",
        )

        serialized_tables = self.export_tables_serialized(
            tables, import_export_config, files_zip, storage
        )

        serialized = super().export_serialized(
            database, import_export_config, files_zip, storage
        )
        serialized.update(
            **DatabaseExportSerializedStructure.database(tables=serialized_tables)
        )

        return serialized

    def _ops_count_for_import_tables_serialized(
        self,
        serialized_tables: List[Dict[str, Any]],
        external_table_fields_to_import: List[Tuple[Table, Dict[str, Any]]] = None,
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
            + len(external_table_fields_to_import or [])
        )

    def init_application(self, user, application: Database) -> None:
        """
        Creates a new minimal table instance and a grid view for the newly
        created application.

        :param user: The user that creates the application.
        :param application: The application to initialize with data.
        """

        with translation.override(user.profile.language):
            first_table_name = _("Table")

        return TableHandler().create_table(
            user, application, first_table_name, fill_example=True
        )

    def import_tables_serialized(
        self,
        database: Database,
        serialized_tables: List[Dict[str, Any]],
        id_mapping: Dict[str, Any],
        import_export_config: ImportExportConfig,
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
        progress_builder: Optional[ChildProgressBuilder] = None,
        external_table_fields_to_import: List[Tuple[Table, Dict[str, Any]]] = None,
    ) -> List[Table]:
        """
        Imports tables exported by the `export_tables_serialized` method. Look at
        `import_serialized` to know how to call this function.

        :param database: The database to import the serialized tables into.
        :param serialized_tables: The serialized tables to import.
        :param id_mapping: A mapping of any table ids that might be referenced in
            serialized_tables to their new/existing ids to use in this import.
        :param files_zip: An optional zip of files which can be used to retrieve
            imported files from
        :param storage: An optional place to persist any user files if importing files
            from a the above file_zip.
        :param progress_builder: A progress builder used to report progress of the
            import.
        :param external_table_fields_to_import: An optional list of fields which should
            also be imported. These fields will be imported into the existing table
            provided in the first item in the tuple, the second being the serialized
            field to import.
            Useful for when importing a single table which also needs to add related
            fields to other existing tables in the database.
        :param import_export_config: provides configuration options for the
            import/export process to customize how it works.
        :return: The list of created tables
        """

        child_total = self._ops_count_for_import_tables_serialized(
            serialized_tables, external_table_fields_to_import
        )
        progress = ChildProgressBuilder.build(progress_builder, child_total=child_total)

        if "import_workspace_id" not in id_mapping and database.workspace is not None:
            id_mapping["import_workspace_id"] = database.workspace.id

        if "database_tables" not in id_mapping:
            id_mapping["database_tables"] = {}

        if "database_fields" not in id_mapping:
            id_mapping["database_fields"] = {}

        if "workspace_id" not in id_mapping and database.workspace is not None:
            id_mapping["workspace_id"] = database.workspace.id

        # Snapshots will provide a specific workspace to import user references from, so
        # we need to use that instead of the workspace the database is in if provided.
        workspace_for_user_references = (
            import_export_config.workspace_for_user_references
        )
        workspace_id_for_user_references = (
            workspace_for_user_references.id
            if workspace_for_user_references is not None
            else id_mapping.get("workspace_id", None)
        )

        user_email_mapping = {}
        if workspace_id_for_user_references:
            user_email_mapping = CoreHandler.get_user_email_mapping(
                workspace_id_for_user_references, only_emails=[]
            )

        imported_tables: List[Table] = []

        # First, we want to create all the table instances because it could be that
        # field or view properties depend on the existence of a table.
        for serialized_table in serialized_tables:
            table_instance = Table.objects.create(
                database=database,
                name=serialized_table["name"],
                order=serialized_table["order"],
                needs_background_update_column_added=True,
                last_modified_by_column_added=True,
            )
            id_mapping["database_tables"][serialized_table["id"]] = table_instance.id
            serialized_table["_object"] = table_instance
            serialized_table["field_instances"] = []
            imported_tables.append(table_instance)
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        # Because view properties might depend on fields, we first want to create all
        # the fields.
        all_fields = []
        deferred_fk_update_collector = DeferredFieldFkUpdater()
        for serialized_table in serialized_tables:
            for serialized_field in serialized_table["fields"]:
                field_type = field_type_registry.get(serialized_field["type"])
                field_instance = field_type.import_serialized(
                    serialized_table["_object"],
                    serialized_field,
                    import_export_config,
                    id_mapping,
                    deferred_fk_update_collector,
                )

                serialized_table["field_instances"].append(field_instance)
                all_fields.append((field_type, field_instance))
                progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        for external_table, serialized_field in external_table_fields_to_import or []:
            field_type = field_type_registry.get(serialized_field["type"])
            external_field = field_type.import_serialized(
                external_table,
                serialized_field,
                import_export_config,
                id_mapping,
                deferred_fk_update_collector,
            )
            SearchHandler.after_field_created(external_field)
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        deferred_fk_update_collector.run_deferred_fk_updates(
            id_mapping["database_fields"]
        )

        # For each field we call `after_import_serialized` which ensures that
        # formulas recalculate themselves now that all fields exist.
        field_cache = FieldCache()
        all_field_ids = []
        for field_type, field_instance in all_fields:
            all_field_ids.append(field_instance.id)
            field_type.after_import_serialized(field_instance, field_cache, id_mapping)

        # Also call the `after_import_serialized` for all the dependant fields so
        # that these formulas are recalculated as well.
        for (
            dependant_field,
            dependant_field_type,
            via_path_to_starting_table,
        ) in FieldDependencyHandler.get_all_dependent_fields_with_type(
            # It's okay to set `table_id=0` here because that's only needed to
            # calculate the correct path, which we don't need here anyway.
            0,
            all_field_ids,
            field_cache,
            associated_relations_changed=True,
        ):
            dependant_field_type.after_import_serialized(
                dependant_field, field_cache, id_mapping
            )

        # The loop above might have recalculated the formula fields in the list,
        # we need to refresh the instances we have as a result as they might be stale.
        for field_type, field_instance in all_fields:
            if field_type.needs_refresh_after_import_serialized:
                field_instance.refresh_from_db()

        # schema_editor.create_model will also create any m2m/through tables which
        # connect two models together. Once we create_model on the first model
        # the m2m will be made, so if we blindly call create_model on the second
        # model it will crash as the m2m connecting those two models already exists.
        # So instead we keep track of which m2m's have already been made to not
        # make them twice!
        already_created_through_table_names = set()
        # Now that the all tables and fields exist, we can create the views and create
        # the table schema in the database.
        for serialized_table in serialized_tables:
            table = serialized_table["_object"]
            for serialized_view in serialized_table["views"]:
                view_type = view_type_registry.get(serialized_view["type"])
                view_type.import_serialized(
                    table, serialized_view, id_mapping, files_zip
                )
                progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

            with safe_django_schema_editor() as schema_editor:
                table_model = table.get_model(
                    fields=serialized_table["field_instances"],
                    field_ids=[],
                    managed=True,
                    add_dependencies=False,
                )
                serialized_table["_model"] = table_model
                # We don't need to create all the fields individually because the schema
                # editor can handle the creation of the table schema in one go.
                schema_editor.create_model_tracking_created_m2ms(
                    table_model, already_created_through_table_names
                )

                # These field attributes must be disabled for date fields
                # because the export contains correct values and we don't want them
                # to be overwritten when importing.
                date_fields = filter(
                    lambda f: isinstance(f, models.DateField),
                    serialized_table["_model"]._meta.get_fields(),
                )
                attrs_to_disable_for_import = [
                    "auto_now_add",
                    "auto_now",
                    "sync_with",
                    "sync_with_add",
                ]
                for date_field in date_fields:
                    for attr in attrs_to_disable_for_import:
                        if getattr(date_field, attr, False):
                            setattr(date_field, attr, False)

            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        # Now that everything is in place we can start filling the table with the rows
        # in an efficient matter by using the bulk_create functionality.
        table_cache: Dict[str, Any] = {}
        already_filled_up_through_table_names = set()
        for serialized_table in serialized_tables:
            table_model = serialized_table["_model"]
            rows_to_be_inserted = []
            # Holds a mapping where the key is a model, and the value a list of
            # objects that must be inserted. These objects are returned by the
            # `set_import_serialized_value`, and will typically hold m2m relationships.
            additional_objects_to_be_inserted = defaultdict(list)

            m2m_fields_to_not_import_as_already_done = set()
            for field in table_model._meta.get_fields():
                if isinstance(field, models.ManyToManyField):
                    remote_through = field.remote_field.through
                    db_table = remote_through._meta.db_table
                    if db_table in already_filled_up_through_table_names:
                        m2m_fields_to_not_import_as_already_done.add(field.name)
                    else:
                        already_filled_up_through_table_names.add(db_table)

            for serialized_row in serialized_table["rows"]:
                created_on = serialized_row.get("created_on")
                updated_on = serialized_row.get("updated_on")

                if created_on:
                    created_on = datetime.fromisoformat(created_on)
                else:
                    created_on = timezone.now()

                if updated_on:
                    updated_on = datetime.fromisoformat(updated_on)
                else:
                    updated_on = timezone.now()

                modified_by_email = serialized_row.get("last_modified_by", None)

                row_instance = table_model(
                    id=serialized_row["id"],
                    order=serialized_row["order"],
                    created_on=created_on,
                    updated_on=updated_on,
                    last_modified_by=user_email_mapping.get(modified_by_email, None)
                    if modified_by_email
                    else None,
                )

                for serialized_field in serialized_table["fields"]:
                    field_type = field_type_registry.get(serialized_field["type"])
                    new_field_id = id_mapping["database_fields"][serialized_field["id"]]
                    new_field_name = f"field_{new_field_id}"
                    field_name = f'field_{serialized_field["id"]}'

                    if (
                        field_name in serialized_row
                        and new_field_name
                        not in m2m_fields_to_not_import_as_already_done
                    ):
                        related_objects_to_save = (
                            field_type.set_import_serialized_value(
                                row_instance,
                                new_field_name,
                                serialized_row[field_name],
                                id_mapping,
                                table_cache,
                                files_zip,
                                storage,
                            )
                        )

                        if related_objects_to_save is not None:
                            for additional_object in related_objects_to_save:
                                additional_objects_to_be_inserted[
                                    additional_object._meta.model
                                ].append(additional_object)

                rows_to_be_inserted.append(row_instance)
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

            # Every row import can have additional objects that must be inserted,
            # like for example the m2m relationships. We want to efficiently import
            # them in bulk here.
            for model, objects in additional_objects_to_be_inserted.items():
                model.objects.bulk_create(objects, batch_size=512)

            # When the rows are inserted we keep the provide the old ids and because of
            # that the auto increment is still set at `1`. This needs to be set to the
            # maximum value because otherwise creating a new row could later fail.
            sequence_sql = connection.ops.sequence_reset_sql(no_style(), [table_model])
            with connection.cursor() as cursor:
                cursor.execute(sequence_sql[0])

        # The progress off `apply_updates_and_get_updated_fields` takes 5% of the
        # total progress of this import.
        for field_type, field_instance in all_fields:
            update_collector = FieldUpdateCollector(field_instance.table)
            field_type.after_rows_imported(
                field_instance, update_collector, field_cache, []
            )
            update_collector.apply_updates_and_get_updated_fields(
                field_cache, skip_search_updates=True
            )
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING)

        # Finally, now that everything has been created, loop over the
        # `serialization_processor_registry` registry and ensure extra
        # metadata is imported too.
        source_workspace = Workspace.objects.get(pk=id_mapping["import_workspace_id"])
        for serialized_table in serialized_tables:
            table = serialized_table["_object"]
            if not import_export_config.reduce_disk_space_usage:
                SearchHandler.entire_field_values_changed_or_created(table)
            for (
                serialized_structure_processor
            ) in serialization_processor_registry.get_all():
                serialized_structure_processor.import_serialized(
                    source_workspace, table, serialized_table, import_export_config
                )

        return imported_tables

    def import_serialized(
        self,
        workspace: Workspace,
        serialized_values: Dict[str, Any],
        import_export_config: ImportExportConfig,
        id_mapping: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> Application:
        """
        Imports a database application exported by the `export_serialized` method.
        """

        database_progress, table_progress = 1, 99
        progress = ChildProgressBuilder.build(
            progress_builder, child_total=database_progress + table_progress
        )

        application = super().import_serialized(
            workspace,
            serialized_values,
            import_export_config,
            id_mapping,
            files_zip,
            storage,
            progress.create_child_builder(represents_progress=database_progress),
        )

        database = application.specific

        if not serialized_values["tables"]:
            progress.increment(state=IMPORT_SERIALIZED_IMPORTING, by=table_progress)
        else:
            self.import_tables_serialized(
                database,
                serialized_values["tables"],
                id_mapping,
                import_export_config,
                files_zip,
                storage,
                progress.create_child_builder(represents_progress=table_progress),
            )

        return database

    def enhance_queryset(self, queryset):
        return queryset.prefetch_related("table_set")
