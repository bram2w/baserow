from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import ProgrammingError
from django.db.models.signals import post_migrate, pre_migrate

from baserow.contrib.database.table.cache import clear_generated_model_cache
from baserow.contrib.database.table.operations import RestoreDatabaseTableOperationType
from baserow.core.registries import (
    application_type_registry,
    object_scope_type_registry,
    operation_type_registry,
    plugin_registry,
)
from baserow.core.trash.registries import trash_item_type_registry
from baserow.core.usage.registries import group_storage_usage_item_registry
from baserow.ws.registries import page_registry


class DatabaseConfig(AppConfig):
    name = "baserow.contrib.database"

    def prevent_generated_model_for_registering(self):
        """
        A nasty hack that prevents a generated table model and related auto created
        models from being registered to the apps. When a model class is defined it
        will be registered to the apps, but we do not always want that to happen
        because models with the same class name can differ. They are also meant to be
        temporary. Removing the model from the cache does not work because if there
        are multiple requests at the same, it is not removed from the cache on time
        which could result in hard failures. It is also hard to extend the
        django.apps.registry.apps so this hack extends the original `register_model`
        method and it will only call the original `register_model` method if the
        model is not a generated table model.

        If anyone has a better way to prevent the models from being registered then I
        am happy to hear about it! :)
        """

        original_register_model = self.apps.register_model

        def register_model(app_label, model):
            if not hasattr(model, "_generated_table_model") and not hasattr(
                model._meta.auto_created, "_generated_table_model"
            ):
                original_register_model(app_label, model)
            else:
                # Trigger the pending operations because the original register_model
                # method also triggers them. Not triggering them can cause a memory
                # leak because everytime a table model is generated, it will register
                # new pending operations.
                self.apps.do_pending_operations(model)
                self.apps.clear_cache()

        self.apps.register_model = register_model

    def ready(self):
        self.prevent_generated_model_for_registering()

        from baserow.core.action.registries import (
            action_scope_registry,
            action_type_registry,
        )

        from .action.scopes import TableActionScopeType, ViewActionScopeType

        action_scope_registry.register(TableActionScopeType())
        action_scope_registry.register(ViewActionScopeType())

        from baserow.contrib.database.tokens.actions import (
            CreateDbTokenActionType,
            DeleteDbTokenActionType,
            RotateDbTokenKeyActionType,
            UpdateDbTokenNameActionType,
            UpdateDbTokenPermissionsActionType,
        )

        action_type_registry.register(CreateDbTokenActionType())
        action_type_registry.register(UpdateDbTokenNameActionType())
        action_type_registry.register(UpdateDbTokenPermissionsActionType())
        action_type_registry.register(RotateDbTokenKeyActionType())
        action_type_registry.register(DeleteDbTokenActionType())

        from baserow.contrib.database.webhooks.actions import (
            CreateWebhookActionType,
            DeleteWebhookActionType,
            UpdateWebhookActionType,
        )

        action_type_registry.register(CreateWebhookActionType())
        action_type_registry.register(DeleteWebhookActionType())
        action_type_registry.register(UpdateWebhookActionType())

        from .export.actions import ExportTableActionType

        action_type_registry.register(ExportTableActionType())

        from .airtable.actions import ImportDatabaseFromAirtableActionType

        action_type_registry.register(ImportDatabaseFromAirtableActionType())

        from .table.actions import (
            CreateTableActionType,
            DeleteTableActionType,
            DuplicateTableActionType,
            OrderTableActionType,
            UpdateTableActionType,
        )

        action_type_registry.register(CreateTableActionType())
        action_type_registry.register(DeleteTableActionType())
        action_type_registry.register(OrderTableActionType())
        action_type_registry.register(UpdateTableActionType())
        action_type_registry.register(DuplicateTableActionType())

        from .rows.actions import (
            CreateRowActionType,
            CreateRowsActionType,
            DeleteRowActionType,
            DeleteRowsActionType,
            ImportRowsActionType,
            MoveRowActionType,
            UpdateRowActionType,
            UpdateRowsActionType,
        )

        action_type_registry.register(CreateRowActionType())
        action_type_registry.register(CreateRowsActionType())
        action_type_registry.register(ImportRowsActionType())
        action_type_registry.register(DeleteRowActionType())
        action_type_registry.register(DeleteRowsActionType())
        action_type_registry.register(MoveRowActionType())
        action_type_registry.register(UpdateRowActionType())
        action_type_registry.register(UpdateRowsActionType())

        from baserow.contrib.database.views.actions import (
            CreateDecorationActionType,
            CreateViewActionType,
            CreateViewFilterActionType,
            CreateViewSortActionType,
            DeleteDecorationActionType,
            DeleteViewActionType,
            DeleteViewFilterActionType,
            DeleteViewSortActionType,
            DuplicateViewActionType,
            OrderViewsActionType,
            RotateViewSlugActionType,
            UpdateDecorationActionType,
            UpdateViewActionType,
            UpdateViewFieldOptionsActionType,
            UpdateViewFilterActionType,
            UpdateViewSortActionType,
        )

        action_type_registry.register(CreateViewActionType())
        action_type_registry.register(DuplicateViewActionType())
        action_type_registry.register(DeleteViewActionType())
        action_type_registry.register(OrderViewsActionType())
        action_type_registry.register(UpdateViewActionType())
        action_type_registry.register(CreateViewFilterActionType())
        action_type_registry.register(UpdateViewFilterActionType())
        action_type_registry.register(DeleteViewFilterActionType())
        action_type_registry.register(CreateViewSortActionType())
        action_type_registry.register(UpdateViewSortActionType())
        action_type_registry.register(DeleteViewSortActionType())
        action_type_registry.register(RotateViewSlugActionType())
        action_type_registry.register(UpdateViewFieldOptionsActionType())
        action_type_registry.register(CreateDecorationActionType())
        action_type_registry.register(UpdateDecorationActionType())
        action_type_registry.register(DeleteDecorationActionType())

        from .airtable.registry import airtable_column_type_registry
        from .export.registries import table_exporter_registry
        from .fields.registries import field_converter_registry, field_type_registry
        from .formula.registries import formula_function_registry
        from .plugins import DatabasePlugin
        from .views.registries import (
            form_view_mode_registry,
            view_aggregation_type_registry,
            view_filter_type_registry,
            view_ownership_type_registry,
            view_type_registry,
        )
        from .webhooks.registries import webhook_event_type_registry

        plugin_registry.register(DatabasePlugin())

        from .fields.field_types import (
            BooleanFieldType,
            CreatedOnFieldType,
            DateFieldType,
            EmailFieldType,
            FileFieldType,
            FormulaFieldType,
            LastModifiedFieldType,
            LinkRowFieldType,
            LongTextFieldType,
            LookupFieldType,
            MultipleCollaboratorsFieldType,
            MultipleSelectFieldType,
            NumberFieldType,
            PhoneNumberFieldType,
            RatingFieldType,
            SingleSelectFieldType,
            TextFieldType,
            URLFieldType,
        )

        field_type_registry.register(TextFieldType())
        field_type_registry.register(LongTextFieldType())
        field_type_registry.register(URLFieldType())
        field_type_registry.register(EmailFieldType())
        field_type_registry.register(NumberFieldType())
        field_type_registry.register(RatingFieldType())
        field_type_registry.register(BooleanFieldType())
        field_type_registry.register(DateFieldType())
        field_type_registry.register(LastModifiedFieldType())
        field_type_registry.register(CreatedOnFieldType())
        field_type_registry.register(LinkRowFieldType())
        field_type_registry.register(FileFieldType())
        field_type_registry.register(SingleSelectFieldType())
        field_type_registry.register(MultipleSelectFieldType())
        field_type_registry.register(PhoneNumberFieldType())
        field_type_registry.register(FormulaFieldType())
        field_type_registry.register(LookupFieldType())
        field_type_registry.register(MultipleCollaboratorsFieldType())

        from .fields.field_converters import (
            FileFieldConverter,
            FormulaFieldConverter,
            LinkRowFieldConverter,
            MultipleCollaboratorsFieldConverter,
            MultipleSelectFieldToSingleSelectFieldConverter,
            MultipleSelectFieldToTextFieldConverter,
            SingleSelectFieldToMultipleSelectFieldConverter,
            TextFieldToMultipleSelectFieldConverter,
        )

        field_converter_registry.register(MultipleCollaboratorsFieldConverter())
        field_converter_registry.register(LinkRowFieldConverter())
        field_converter_registry.register(FileFieldConverter())
        field_converter_registry.register(TextFieldToMultipleSelectFieldConverter())
        field_converter_registry.register(MultipleSelectFieldToTextFieldConverter())
        field_converter_registry.register(
            MultipleSelectFieldToSingleSelectFieldConverter()
        )
        field_converter_registry.register(
            SingleSelectFieldToMultipleSelectFieldConverter()
        )
        field_converter_registry.register(FormulaFieldConverter())

        from .fields.actions import (
            CreateFieldActionType,
            DeleteFieldActionType,
            DuplicateFieldActionType,
            UpdateFieldActionType,
        )

        action_type_registry.register(CreateFieldActionType())
        action_type_registry.register(DeleteFieldActionType())
        action_type_registry.register(UpdateFieldActionType())
        action_type_registry.register(DuplicateFieldActionType())

        from .views.view_types import FormViewType, GalleryViewType, GridViewType

        view_type_registry.register(GridViewType())
        view_type_registry.register(GalleryViewType())
        view_type_registry.register(FormViewType())

        from .views.view_filters import (
            BooleanViewFilterType,
            ContainsNotViewFilterType,
            ContainsViewFilterType,
            ContainsWordViewFilterType,
            DateAfterTodayViewFilterType,
            DateAfterViewFilterType,
            DateBeforeTodayViewFilterType,
            DateBeforeViewFilterType,
            DateEqualsCurrentMonthViewFilterType,
            DateEqualsCurrentWeekViewFilterType,
            DateEqualsCurrentYearViewFilterType,
            DateEqualsDayOfMonthViewFilterType,
            DateEqualsDaysAgoViewFilterType,
            DateEqualsMonthsAgoViewFilterType,
            DateEqualsTodayViewFilterType,
            DateEqualsYearsAgoViewFilterType,
            DateEqualViewFilterType,
            DateNotEqualViewFilterType,
            DoesntContainWordViewFilterType,
            EmptyViewFilterType,
            EqualViewFilterType,
            FilenameContainsViewFilterType,
            HasFileTypeViewFilterType,
            HigherThanViewFilterType,
            LengthIsLowerThanViewFilterType,
            LinkRowContainsViewFilterType,
            LinkRowHasNotViewFilterType,
            LinkRowHasViewFilterType,
            LinkRowNotContainsViewFilterType,
            LowerThanViewFilterType,
            MultipleCollaboratorsHasNotViewFilterType,
            MultipleCollaboratorsHasViewFilterType,
            MultipleSelectHasNotViewFilterType,
            MultipleSelectHasViewFilterType,
            NotEmptyViewFilterType,
            NotEqualViewFilterType,
            SingleSelectEqualViewFilterType,
            SingleSelectNotEqualViewFilterType,
        )

        view_filter_type_registry.register(EqualViewFilterType())
        view_filter_type_registry.register(NotEqualViewFilterType())
        view_filter_type_registry.register(FilenameContainsViewFilterType())
        view_filter_type_registry.register(HasFileTypeViewFilterType())
        view_filter_type_registry.register(ContainsViewFilterType())
        view_filter_type_registry.register(ContainsNotViewFilterType())
        view_filter_type_registry.register(ContainsWordViewFilterType())
        view_filter_type_registry.register(DoesntContainWordViewFilterType())
        view_filter_type_registry.register(LengthIsLowerThanViewFilterType())
        view_filter_type_registry.register(HigherThanViewFilterType())
        view_filter_type_registry.register(LowerThanViewFilterType())
        view_filter_type_registry.register(DateEqualViewFilterType())
        view_filter_type_registry.register(DateBeforeViewFilterType())
        view_filter_type_registry.register(DateAfterViewFilterType())
        view_filter_type_registry.register(DateNotEqualViewFilterType())
        view_filter_type_registry.register(DateEqualsTodayViewFilterType())
        view_filter_type_registry.register(DateBeforeTodayViewFilterType())
        view_filter_type_registry.register(DateAfterTodayViewFilterType())
        view_filter_type_registry.register(DateEqualsDaysAgoViewFilterType())
        view_filter_type_registry.register(DateEqualsMonthsAgoViewFilterType())
        view_filter_type_registry.register(DateEqualsYearsAgoViewFilterType())
        view_filter_type_registry.register(DateEqualsCurrentWeekViewFilterType())
        view_filter_type_registry.register(DateEqualsCurrentMonthViewFilterType())
        view_filter_type_registry.register(DateEqualsDayOfMonthViewFilterType())
        view_filter_type_registry.register(DateEqualsCurrentYearViewFilterType())
        view_filter_type_registry.register(SingleSelectEqualViewFilterType())
        view_filter_type_registry.register(SingleSelectNotEqualViewFilterType())
        view_filter_type_registry.register(LinkRowHasViewFilterType())
        view_filter_type_registry.register(LinkRowHasNotViewFilterType())
        view_filter_type_registry.register(LinkRowContainsViewFilterType())
        view_filter_type_registry.register(LinkRowNotContainsViewFilterType())
        view_filter_type_registry.register(BooleanViewFilterType())
        view_filter_type_registry.register(EmptyViewFilterType())
        view_filter_type_registry.register(NotEmptyViewFilterType())
        view_filter_type_registry.register(MultipleSelectHasViewFilterType())
        view_filter_type_registry.register(MultipleSelectHasNotViewFilterType())
        view_filter_type_registry.register(MultipleCollaboratorsHasViewFilterType())
        view_filter_type_registry.register(MultipleCollaboratorsHasNotViewFilterType())

        from .views.view_aggregations import (
            AverageViewAggregationType,
            DecileViewAggregationType,
            EmptyCountViewAggregationType,
            MaxViewAggregationType,
            MedianViewAggregationType,
            MinViewAggregationType,
            NotEmptyCountViewAggregationType,
            StdDevViewAggregationType,
            SumViewAggregationType,
            UniqueCountViewAggregationType,
            VarianceViewAggregationType,
        )

        view_aggregation_type_registry.register(EmptyCountViewAggregationType())
        view_aggregation_type_registry.register(NotEmptyCountViewAggregationType())
        view_aggregation_type_registry.register(UniqueCountViewAggregationType())
        view_aggregation_type_registry.register(MinViewAggregationType())
        view_aggregation_type_registry.register(MaxViewAggregationType())
        view_aggregation_type_registry.register(SumViewAggregationType())
        view_aggregation_type_registry.register(AverageViewAggregationType())
        view_aggregation_type_registry.register(MedianViewAggregationType())
        view_aggregation_type_registry.register(DecileViewAggregationType())
        view_aggregation_type_registry.register(VarianceViewAggregationType())
        view_aggregation_type_registry.register(StdDevViewAggregationType())

        from .views.form_view_mode_types import FormViewModeTypeForm

        form_view_mode_registry.register(FormViewModeTypeForm())

        from .views.view_ownership_types import CollaborativeViewOwnershipType

        view_ownership_type_registry.register(CollaborativeViewOwnershipType())

        from .application_types import DatabaseApplicationType

        application_type_registry.register(DatabaseApplicationType())

        from .ws.pages import PublicViewPageType, TablePageType

        page_registry.register(TablePageType())
        page_registry.register(PublicViewPageType())

        from .export.table_exporters.csv_table_exporter import CsvTableExporter

        table_exporter_registry.register(CsvTableExporter())

        from .trash.trash_types import (
            FieldTrashableItemType,
            RowsTrashableItemType,
            RowTrashableItemType,
            TableTrashableItemType,
            ViewTrashableItemType,
        )

        trash_item_type_registry.register(TableTrashableItemType())
        trash_item_type_registry.register(FieldTrashableItemType())
        trash_item_type_registry.register(RowTrashableItemType())
        trash_item_type_registry.register(RowsTrashableItemType())
        trash_item_type_registry.register(ViewTrashableItemType())

        from .formula.ast.function_defs import register_formula_functions

        register_formula_functions(formula_function_registry)

        from .rows.webhook_event_types import (
            RowCreatedEventType,
            RowDeletedEventType,
            RowsCreatedEventType,
            RowsDeletedEventType,
            RowsUpdatedEventType,
            RowUpdatedEventType,
        )

        webhook_event_type_registry.register(RowsCreatedEventType())
        webhook_event_type_registry.register(RowCreatedEventType())
        webhook_event_type_registry.register(RowsUpdatedEventType())
        webhook_event_type_registry.register(RowUpdatedEventType())
        webhook_event_type_registry.register(RowsDeletedEventType())
        webhook_event_type_registry.register(RowDeletedEventType())

        from .airtable.airtable_column_types import (
            CheckboxAirtableColumnType,
            DateAirtableColumnType,
            ForeignKeyAirtableColumnType,
            FormulaAirtableColumnType,
            MultilineTextAirtableColumnType,
            MultipleAttachmentAirtableColumnType,
            MultiSelectAirtableColumnType,
            NumberAirtableColumnType,
            PhoneAirtableColumnType,
            RatingAirtableColumnType,
            RichTextTextAirtableColumnType,
            SelectAirtableColumnType,
            TextAirtableColumnType,
        )

        airtable_column_type_registry.register(TextAirtableColumnType())
        airtable_column_type_registry.register(DateAirtableColumnType())
        airtable_column_type_registry.register(NumberAirtableColumnType())
        airtable_column_type_registry.register(SelectAirtableColumnType())
        airtable_column_type_registry.register(MultiSelectAirtableColumnType())
        airtable_column_type_registry.register(RatingAirtableColumnType())
        airtable_column_type_registry.register(FormulaAirtableColumnType())
        airtable_column_type_registry.register(CheckboxAirtableColumnType())
        airtable_column_type_registry.register(PhoneAirtableColumnType())
        airtable_column_type_registry.register(ForeignKeyAirtableColumnType())
        airtable_column_type_registry.register(MultilineTextAirtableColumnType())
        airtable_column_type_registry.register(MultipleAttachmentAirtableColumnType())
        airtable_column_type_registry.register(RichTextTextAirtableColumnType())

        from baserow.contrib.database.table.usage_types import (
            TableGroupStorageUsageItemType,
        )

        group_storage_usage_item_registry.register(TableGroupStorageUsageItemType())

        from baserow.contrib.database.views.usage_types import (
            FormViewGroupStorageUsageItem,
        )

        group_storage_usage_item_registry.register(FormViewGroupStorageUsageItem())

        from baserow.core.jobs.registries import job_type_registry

        from .airtable.job_types import AirtableImportJobType
        from .fields.job_types import DuplicateFieldJobType
        from .file_import.job_types import FileImportJobType
        from .table.job_types import DuplicateTableJobType

        job_type_registry.register(AirtableImportJobType())
        job_type_registry.register(FileImportJobType())
        job_type_registry.register(DuplicateTableJobType())
        job_type_registry.register(DuplicateFieldJobType())

        post_migrate.connect(safely_update_formula_versions, sender=self)
        pre_migrate.connect(clear_generated_model_cache_receiver, sender=self)

        from .fields.object_scopes import FieldObjectScopeType
        from .object_scopes import DatabaseObjectScopeType
        from .table.object_scopes import DatabaseTableObjectScopeType
        from .tokens.object_scopes import TokenObjectScopeType
        from .views.object_scopes import (
            DatabaseViewDecorationObjectScopeType,
            DatabaseViewFilterObjectScopeType,
            DatabaseViewObjectScopeType,
            DatabaseViewSortObjectScopeType,
        )

        object_scope_type_registry.register(DatabaseObjectScopeType())
        object_scope_type_registry.register(DatabaseTableObjectScopeType())
        object_scope_type_registry.register(FieldObjectScopeType())
        object_scope_type_registry.register(DatabaseViewObjectScopeType())
        object_scope_type_registry.register(DatabaseViewDecorationObjectScopeType())
        object_scope_type_registry.register(DatabaseViewSortObjectScopeType())
        object_scope_type_registry.register(DatabaseViewFilterObjectScopeType())
        object_scope_type_registry.register(TokenObjectScopeType())

        from baserow.contrib.database.views.operations import (
            UpdateViewFieldOptionsOperationType,
        )

        from .airtable.operations import RunAirtableImportJobOperationType
        from .export.operations import ExportTableOperationType
        from .fields.operations import (
            CreateFieldOperationType,
            DeleteFieldOperationType,
            DeleteRelatedLinkRowFieldOperationType,
            DuplicateFieldOperationType,
            ListFieldsOperationType,
            ReadFieldOperationType,
            RestoreFieldOperationType,
            UpdateFieldOperationType,
        )
        from .formula import TypeFormulaOperationType
        from .operations import (
            CreateTableDatabaseTableOperationType,
            ListTablesDatabaseTableOperationType,
            OrderTablesDatabaseTableOperationType,
        )
        from .rows.operations import (
            DeleteDatabaseRowOperationType,
            MoveRowDatabaseRowOperationType,
            ReadAdjacentRowDatabaseRowOperationType,
            ReadDatabaseRowOperationType,
            RestoreDatabaseRowOperationType,
            UpdateDatabaseRowOperationType,
        )
        from .table.operations import (
            CreateRowDatabaseTableOperationType,
            DeleteDatabaseTableOperationType,
            DuplicateDatabaseTableOperationType,
            ImportRowsDatabaseTableOperationType,
            ListenToAllDatabaseTableEventsOperationType,
            ListRowNamesDatabaseTableOperationType,
            ListRowsDatabaseTableOperationType,
            ReadDatabaseTableOperationType,
            UpdateDatabaseTableOperationType,
        )
        from .tokens.operations import (
            CreateTokenOperationType,
            ReadTokenOperationType,
            UpdateTokenOperationType,
            UseTokenOperationType,
        )
        from .views.operations import (
            CreateViewDecorationOperationType,
            CreateViewFilterOperationType,
            CreateViewOperationType,
            CreateViewSortOperationType,
            DeleteViewDecorationOperationType,
            DeleteViewFilterOperationType,
            DeleteViewOperationType,
            DeleteViewSortOperationType,
            DuplicateViewOperationType,
            ListAggregationsViewOperationType,
            ListViewDecorationOperationType,
            ListViewFilterOperationType,
            ListViewsOperationType,
            ListViewSortOperationType,
            OrderViewsOperationType,
            ReadAggregationsViewOperationType,
            ReadViewDecorationOperationType,
            ReadViewFieldOptionsOperationType,
            ReadViewFilterOperationType,
            ReadViewOperationType,
            ReadViewsOrderOperationType,
            ReadViewSortOperationType,
            RestoreViewOperationType,
            UpdateViewDecorationOperationType,
            UpdateViewFilterOperationType,
            UpdateViewOperationType,
            UpdateViewSlugOperationType,
            UpdateViewSortOperationType,
        )
        from .webhooks.operations import (
            CreateWebhookOperationType,
            DeleteWebhookOperationType,
            ListTableWebhooksOperationType,
            ReadWebhookOperationType,
            TestTriggerWebhookOperationType,
            UpdateWebhookOperationType,
        )

        operation_type_registry.register(CreateTableDatabaseTableOperationType())
        operation_type_registry.register(ListTablesDatabaseTableOperationType())
        operation_type_registry.register(OrderTablesDatabaseTableOperationType())
        operation_type_registry.register(CreateRowDatabaseTableOperationType())
        operation_type_registry.register(ImportRowsDatabaseTableOperationType())
        operation_type_registry.register(DeleteDatabaseTableOperationType())
        operation_type_registry.register(DuplicateDatabaseTableOperationType())
        operation_type_registry.register(ListRowsDatabaseTableOperationType())
        operation_type_registry.register(ReadDatabaseTableOperationType())
        operation_type_registry.register(UpdateDatabaseTableOperationType())
        operation_type_registry.register(ReadDatabaseRowOperationType())
        operation_type_registry.register(UpdateDatabaseRowOperationType())
        operation_type_registry.register(DeleteDatabaseRowOperationType())
        operation_type_registry.register(CreateViewSortOperationType())
        operation_type_registry.register(ReadViewSortOperationType())
        operation_type_registry.register(UpdateViewSortOperationType())
        operation_type_registry.register(CreateFieldOperationType())
        operation_type_registry.register(ReadFieldOperationType())
        operation_type_registry.register(UpdateFieldOperationType())
        operation_type_registry.register(DeleteFieldOperationType())
        operation_type_registry.register(DeleteRelatedLinkRowFieldOperationType())
        operation_type_registry.register(DuplicateFieldOperationType())
        operation_type_registry.register(UpdateViewFieldOptionsOperationType())
        operation_type_registry.register(DeleteViewSortOperationType())
        operation_type_registry.register(UpdateViewSlugOperationType())
        operation_type_registry.register(ReadViewsOrderOperationType())
        operation_type_registry.register(OrderViewsOperationType())
        operation_type_registry.register(CreateViewOperationType())
        operation_type_registry.register(ReadViewOperationType())
        operation_type_registry.register(UpdateViewOperationType())
        operation_type_registry.register(DeleteViewOperationType())
        operation_type_registry.register(DuplicateViewOperationType())
        operation_type_registry.register(CreateViewFilterOperationType())
        operation_type_registry.register(ReadViewFilterOperationType())
        operation_type_registry.register(UpdateViewFilterOperationType())
        operation_type_registry.register(DeleteViewFilterOperationType())
        operation_type_registry.register(DeleteViewDecorationOperationType())
        operation_type_registry.register(CreateWebhookOperationType())
        operation_type_registry.register(DeleteWebhookOperationType())
        operation_type_registry.register(ReadWebhookOperationType())
        operation_type_registry.register(ListTableWebhooksOperationType())
        operation_type_registry.register(TestTriggerWebhookOperationType())
        operation_type_registry.register(UpdateWebhookOperationType())
        operation_type_registry.register(RestoreDatabaseTableOperationType())
        operation_type_registry.register(RestoreDatabaseRowOperationType())
        operation_type_registry.register(RestoreFieldOperationType())
        operation_type_registry.register(RestoreViewOperationType())
        operation_type_registry.register(RunAirtableImportJobOperationType())
        operation_type_registry.register(TypeFormulaOperationType())
        operation_type_registry.register(ListRowNamesDatabaseTableOperationType())
        operation_type_registry.register(ReadAdjacentRowDatabaseRowOperationType())
        operation_type_registry.register(ReadAggregationsViewOperationType())
        operation_type_registry.register(ListAggregationsViewOperationType())
        operation_type_registry.register(ExportTableOperationType())
        operation_type_registry.register(ListFieldsOperationType())
        operation_type_registry.register(ListViewsOperationType())
        operation_type_registry.register(ListViewFilterOperationType())
        operation_type_registry.register(ListViewDecorationOperationType())
        operation_type_registry.register(CreateViewDecorationOperationType())
        operation_type_registry.register(ReadViewDecorationOperationType())
        operation_type_registry.register(UpdateViewDecorationOperationType())
        operation_type_registry.register(ListViewSortOperationType())
        operation_type_registry.register(ReadViewFieldOptionsOperationType())
        operation_type_registry.register(MoveRowDatabaseRowOperationType())
        operation_type_registry.register(CreateTokenOperationType())
        operation_type_registry.register(ReadTokenOperationType())
        operation_type_registry.register(ListenToAllDatabaseTableEventsOperationType())
        operation_type_registry.register(UseTokenOperationType())
        operation_type_registry.register(UpdateTokenOperationType())

        from baserow.core.registries import permission_manager_type_registry

        from .tokens.permission_manager import TokenPermissionManagerType

        permission_manager_type_registry.register(TokenPermissionManagerType())

        from baserow.core.registries import subject_type_registry

        from .tokens.subjects import TokenSubjectType

        subject_type_registry.register(TokenSubjectType())

        # The signals must always be imported last because they use the registries
        # which need to be filled first.
        import baserow.contrib.database.ws.signals  # noqa: F403, F401

        post_migrate.connect(safely_update_formula_versions, sender=self)
        pre_migrate.connect(clear_generated_model_cache_receiver, sender=self)

        import baserow.contrib.database.fields.tasks  # noqa: F401


# noinspection PyPep8Naming
def clear_generated_model_cache_receiver(sender, **kwargs):
    clear_generated_model_cache()


# noinspection PyPep8Naming
def safely_update_formula_versions(sender, **kwargs):
    if settings.TESTS:
        return

    apps = kwargs.get("apps", None)
    # app.ready will be called for management commands also, we only want to
    # execute the following hook when we are starting the django server as
    # otherwise backwards migrations etc will crash because of this.
    if apps is not None and not settings.DONT_UPDATE_FORMULAS_AFTER_MIGRATION:

        try:
            FormulaField = apps.get_model("database", "FormulaField")
            # noinspection PyProtectedMember
            FormulaField._meta.get_field("version")
        except (LookupError, FieldDoesNotExist):
            print(
                "Skipping formula update as FormulaField does not exist or have "
                "version column."
            )
            # We are starting up a version of baserow before formulas with versions
            # existed, there is nothing to do.
            return

        try:
            FormulaField.objects.exists()
        except ProgrammingError:
            print("Skipping formula update as formula field table doesnt exist yet.")
            # The migrations to create FormulaField and FormulaField.version
            # exist but they have not yet been applied.
            return

        print("Checking to see if formulas need updating...")
        from baserow.contrib.database.formula.migrations.handler import (
            FormulaMigrationHandler,
        )

        FormulaMigrationHandler.migrate_formulas_to_latest_version()
