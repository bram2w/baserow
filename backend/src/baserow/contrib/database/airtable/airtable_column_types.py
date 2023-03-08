import traceback
from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError

from loguru import logger
from pytz import UTC

from baserow.contrib.database.export_serialized import DatabaseExportSerializedStructure
from baserow.contrib.database.fields.models import (
    NUMBER_MAX_DECIMAL_PLACES,
    BooleanField,
    CreatedOnField,
    DateField,
    EmailField,
    FileField,
    LastModifiedField,
    LinkRowField,
    LongTextField,
    MultipleSelectField,
    NumberField,
    PhoneNumberField,
    RatingField,
    SingleSelectField,
    TextField,
    URLField,
)
from baserow.contrib.database.fields.registries import field_type_registry

from .helpers import import_airtable_date_type_options, set_select_options_on_field
from .registry import AirtableColumnType


class TextAirtableColumnType(AirtableColumnType):
    type = "text"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        validator_name = raw_airtable_column.get("typeOptions", {}).get("validatorName")
        if validator_name == "url":
            return URLField()
        elif validator_name == "email":
            return EmailField()
        else:
            return TextField()

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        files_to_download,
    ):
        if isinstance(baserow_field, (EmailField, URLField)):
            try:
                field_type = field_type_registry.get_by_model(baserow_field)
                field_type.validator(value)
            except ValidationError:
                return ""

        return value


class MultilineTextAirtableColumnType(AirtableColumnType):
    type = "multilineText"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        return LongTextField()


class RichTextTextAirtableColumnType(AirtableColumnType):
    type = "richText"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        return LongTextField()

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        files_to_download,
    ):
        # We don't support rich text formatting yet, so this converts the value to
        # plain text.
        return "".join([v["insert"] for v in value["documentValue"]])


class NumberAirtableColumnType(AirtableColumnType):
    type = "number"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        type_options = raw_airtable_column.get("typeOptions", {})
        decimal_places = 0

        if type_options.get("format", "integer") == "decimal":
            # Minimum of 1 and maximum of 5 decimal places.
            decimal_places = min(
                max(1, type_options.get("precision", 1)), NUMBER_MAX_DECIMAL_PLACES
            )

        return NumberField(
            number_decimal_places=decimal_places,
            number_negative=type_options.get("negative", True),
        )

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        files_to_download,
    ):
        if value is not None:
            value = Decimal(value)

        if value is not None and not baserow_field.number_negative and value < 0:
            value = None

        return None if value is None else str(value)


class RatingAirtableColumnType(AirtableColumnType):
    type = "rating"

    def to_baserow_field(self, raw_airtable_table, values):
        return RatingField(max_value=values.get("typeOptions", {}).get("max", 5))


class CheckboxAirtableColumnType(AirtableColumnType):
    type = "checkbox"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        return BooleanField()

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        files_to_download,
    ):
        return "true" if value else "false"


class DateAirtableColumnType(AirtableColumnType):
    type = "date"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        type_options = raw_airtable_column.get("typeOptions", {})
        # Check if a timezone is provided in the type options, if so, we might want
        # to use that timezone for the conversion later on.
        airtable_timezone = type_options.get("timeZone", None)
        date_show_tzinfo = type_options.get("shouldDisplayTimeZone", False)

        # date_force_timezone=None it the equivalent of airtable_timezone="client".
        if airtable_timezone == "client":
            airtable_timezone = None

        return DateField(
            date_show_tzinfo=date_show_tzinfo,
            date_force_timezone=airtable_timezone,
            **import_airtable_date_type_options(type_options),
        )

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        files_to_download,
    ):
        if value is None:
            return value

        try:
            value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                tzinfo=UTC
            )
        except ValueError:
            tb = traceback.format_exc()
            print(f"Importing Airtable datetime cell failed because of: \n{tb}")
            logger.error(f"Importing Airtable datetime cell failed because of: \n{tb}")
            return None

        if baserow_field.date_include_time:
            return f"{value.isoformat()}"
        else:
            # WORKAROUND: if the year value is < 1000, Python has a bug that will not
            # add leading zeros to generate the year in four digits format, hence,
            # we're adding the missing zeros if needed. source:
            # https://stackoverflow.com/questions/71118275/parsing-three-digit-years-using-datetime
            formatted_date = value.strftime("%Y-%m-%d")
            zeros = 4 - formatted_date.index("-")
            if zeros:
                formatted_date = f"{'0' * zeros}{formatted_date}"
            return formatted_date


class FormulaAirtableColumnType(AirtableColumnType):
    type = "formula"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        type_options = raw_airtable_column.get("typeOptions", {})
        display_type = type_options.get("displayType", "")
        airtable_timezone = type_options.get("timeZone", None)
        date_show_tzinfo = type_options.get("shouldDisplayTimeZone", False)

        # date_force_timezone=None it the equivalent of airtable_timezone="client".
        if airtable_timezone == "client":
            airtable_timezone = None

        # The formula conversion isn't support yet, but because the Created on and
        # Last modified fields work as a formula, we can convert those.
        if display_type == "lastModifiedTime":
            return LastModifiedField(
                date_show_tzinfo=date_show_tzinfo,
                date_force_timezone=airtable_timezone,
                **import_airtable_date_type_options(type_options),
            )
        elif display_type == "createdTime":
            return CreatedOnField(
                date_show_tzinfo=date_show_tzinfo,
                date_force_timezone=airtable_timezone,
                **import_airtable_date_type_options(type_options),
            )

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        files_to_download,
    ):
        if isinstance(baserow_field, CreatedOnField):
            # If `None`, the value will automatically be populated from the
            # `created_on` property of the row when importing, which already contains
            # the correct value.
            return None
        if isinstance(baserow_field, LastModifiedField):
            # Because there isn't a last modified property in the Airtable data,
            # we must use the value as provided here.
            return (
                datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
                .replace(tzinfo=UTC)
                .isoformat()
            )


class ForeignKeyAirtableColumnType(AirtableColumnType):
    type = "foreignKey"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        type_options = raw_airtable_column.get("typeOptions", {})
        foreign_table_id = type_options.get("foreignTableId")

        return LinkRowField(
            link_row_table_id=foreign_table_id,
            link_row_related_field_id=type_options.get("symmetricColumnId"),
        )

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        files_to_download,
    ):
        foreign_table_id = raw_airtable_column["typeOptions"]["foreignTableId"]
        return [row_id_mapping[foreign_table_id][v["foreignRowId"]] for v in value]


class MultipleAttachmentAirtableColumnType(AirtableColumnType):
    type = "multipleAttachment"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        return FileField()

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        files_to_download,
    ):
        new_value = []
        for file in value:
            file_name = "_".join(file["url"].split("/")[-3:])
            files_to_download[file_name] = file["url"]
            new_value.append(
                DatabaseExportSerializedStructure.file_field_value(
                    name=file_name,
                    visible_name=file["filename"],
                    original_name=file["filename"],
                )
            )

        return new_value


class SelectAirtableColumnType(AirtableColumnType):
    type = "select"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        field = SingleSelectField()
        field = set_select_options_on_field(
            field, raw_airtable_column.get("typeOptions", {})
        )
        return field


class MultiSelectAirtableColumnType(AirtableColumnType):
    type = "multiSelect"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        field = MultipleSelectField()
        field = set_select_options_on_field(
            field, raw_airtable_column.get("typeOptions", {})
        )
        return field


class PhoneAirtableColumnType(AirtableColumnType):
    type = "phone"

    def to_baserow_field(self, raw_airtable_table, raw_airtable_column):
        return PhoneNumberField()

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        files_to_download,
    ):
        try:
            field_type = field_type_registry.get_by_model(baserow_field)
            field_type.validator(value)
            return value
        except ValidationError:
            return ""
