from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import ProgrammingError
from django.db.models.signals import post_migrate

from baserow.contrib.database.table.cache import clear_generated_model_cache
from baserow.core.registries import (
    plugin_registry,
    application_type_registry,
)
from baserow.core.trash.registries import trash_item_type_registry
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

        from .views.registries import (
            view_type_registry,
            view_filter_type_registry,
            view_aggregation_type_registry,
        )
        from .fields.registries import field_type_registry, field_converter_registry
        from .export.registries import table_exporter_registry
        from .formula.registries import (
            formula_function_registry,
        )
        from .webhooks.registries import webhook_event_type_registry
        from .airtable.registry import airtable_column_type_registry

        from .plugins import DatabasePlugin

        plugin_registry.register(DatabasePlugin())

        from .fields.field_types import (
            TextFieldType,
            LongTextFieldType,
            URLFieldType,
            NumberFieldType,
            RatingFieldType,
            BooleanFieldType,
            DateFieldType,
            LastModifiedFieldType,
            CreatedOnFieldType,
            LinkRowFieldType,
            EmailFieldType,
            FileFieldType,
            SingleSelectFieldType,
            MultipleSelectFieldType,
            PhoneNumberFieldType,
            FormulaFieldType,
            LookupFieldType,
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

        from .fields.field_converters import (
            LinkRowFieldConverter,
            FileFieldConverter,
            TextFieldToMultipleSelectFieldConverter,
            MultipleSelectFieldToTextFieldConverter,
            MultipleSelectFieldToSingleSelectFieldConverter,
            SingleSelectFieldToMultipleSelectFieldConverter,
            FormulaFieldConverter,
        )

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

        from .views.view_types import GridViewType, GalleryViewType, FormViewType

        view_type_registry.register(GridViewType())
        view_type_registry.register(GalleryViewType())
        view_type_registry.register(FormViewType())

        from .views.view_filters import (
            EqualViewFilterType,
            NotEqualViewFilterType,
            EmptyViewFilterType,
            NotEmptyViewFilterType,
            DateEqualViewFilterType,
            DateBeforeViewFilterType,
            DateAfterViewFilterType,
            DateNotEqualViewFilterType,
            DateEqualsTodayViewFilterType,
            DateEqualsCurrentMonthViewFilterType,
            DateEqualsCurrentYearViewFilterType,
            HigherThanViewFilterType,
            LowerThanViewFilterType,
            DateEqualsDayOfMonthViewFilterType,
            ContainsViewFilterType,
            FilenameContainsViewFilterType,
            HasFileTypeViewFilterType,
            ContainsNotViewFilterType,
            BooleanViewFilterType,
            SingleSelectEqualViewFilterType,
            SingleSelectNotEqualViewFilterType,
            LinkRowHasViewFilterType,
            LinkRowHasNotViewFilterType,
            MultipleSelectHasViewFilterType,
            MultipleSelectHasNotViewFilterType,
            LengthIsLowerThanViewFilterType,
        )

        view_filter_type_registry.register(EqualViewFilterType())
        view_filter_type_registry.register(NotEqualViewFilterType())
        view_filter_type_registry.register(FilenameContainsViewFilterType())
        view_filter_type_registry.register(HasFileTypeViewFilterType())
        view_filter_type_registry.register(ContainsViewFilterType())
        view_filter_type_registry.register(ContainsNotViewFilterType())
        view_filter_type_registry.register(LengthIsLowerThanViewFilterType())
        view_filter_type_registry.register(HigherThanViewFilterType())
        view_filter_type_registry.register(LowerThanViewFilterType())
        view_filter_type_registry.register(DateEqualViewFilterType())
        view_filter_type_registry.register(DateBeforeViewFilterType())
        view_filter_type_registry.register(DateAfterViewFilterType())
        view_filter_type_registry.register(DateNotEqualViewFilterType())
        view_filter_type_registry.register(DateEqualsTodayViewFilterType())
        view_filter_type_registry.register(DateEqualsCurrentMonthViewFilterType())
        view_filter_type_registry.register(DateEqualsDayOfMonthViewFilterType())
        view_filter_type_registry.register(DateEqualsCurrentYearViewFilterType())
        view_filter_type_registry.register(SingleSelectEqualViewFilterType())
        view_filter_type_registry.register(SingleSelectNotEqualViewFilterType())
        view_filter_type_registry.register(LinkRowHasViewFilterType())
        view_filter_type_registry.register(LinkRowHasNotViewFilterType())
        view_filter_type_registry.register(BooleanViewFilterType())
        view_filter_type_registry.register(EmptyViewFilterType())
        view_filter_type_registry.register(NotEmptyViewFilterType())
        view_filter_type_registry.register(MultipleSelectHasViewFilterType())
        view_filter_type_registry.register(MultipleSelectHasNotViewFilterType())

        from .views.view_aggregations import (
            EmptyCountViewAggregationType,
            NotEmptyCountViewAggregationType,
        )

        view_aggregation_type_registry.register(EmptyCountViewAggregationType())
        view_aggregation_type_registry.register(NotEmptyCountViewAggregationType())

        from .application_types import DatabaseApplicationType

        application_type_registry.register(DatabaseApplicationType())

        from .ws.pages import TablePageType, PublicViewPageType

        page_registry.register(TablePageType())
        page_registry.register(PublicViewPageType())

        from .export.table_exporters.csv_table_exporter import CsvTableExporter

        table_exporter_registry.register(CsvTableExporter())

        from .trash.trash_types import (
            TableTrashableItemType,
            RowTrashableItemType,
            FieldTrashableItemType,
        )

        trash_item_type_registry.register(TableTrashableItemType())
        trash_item_type_registry.register(FieldTrashableItemType())
        trash_item_type_registry.register(RowTrashableItemType())

        from .formula.ast.function_defs import register_formula_functions

        register_formula_functions(formula_function_registry)

        from .rows.webhook_event_types import (
            RowCreatedEventType,
            RowUpdatedEventType,
            RowDeletedEventType,
        )

        webhook_event_type_registry.register(RowCreatedEventType())
        webhook_event_type_registry.register(RowUpdatedEventType())
        webhook_event_type_registry.register(RowDeletedEventType())

        from .airtable.airtable_column_types import (
            TextAirtableColumnType,
            DateAirtableColumnType,
            NumberAirtableColumnType,
            SelectAirtableColumnType,
            MultiSelectAirtableColumnType,
            RatingAirtableColumnType,
            FormulaAirtableColumnType,
            CheckboxAirtableColumnType,
            PhoneAirtableColumnType,
            ForeignKeyAirtableColumnType,
            MultilineTextAirtableColumnType,
            MultipleAttachmentAirtableColumnType,
            RichTextTextAirtableColumnType,
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

        # The signals must always be imported last because they use the registries
        # which need to be filled first.
        import baserow.contrib.database.ws.signals  # noqa: F403, F401

        post_migrate.connect(safely_update_formula_versions, sender=self)
        post_migrate.connect(clear_generated_model_cache_receiver, sender=self)


# noinspection PyPep8Naming
def clear_generated_model_cache_receiver(sender, **kwargs):
    clear_generated_model_cache()


# noinspection PyPep8Naming
def safely_update_formula_versions(sender, **kwargs):
    apps = kwargs.get("apps", None)
    # app.ready will be called for management commands also, we only want to
    # execute the following hook when we are starting the django server as
    # otherwise backwards migrations etc will crash because of this.
    if apps is not None and settings.UPDATE_FORMULAS_AFTER_MIGRATION:
        from baserow.contrib.database.formula import FormulaHandler

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
        FormulaHandler.recalculate_formulas_according_to_version()
