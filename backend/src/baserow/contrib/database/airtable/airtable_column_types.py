from datetime import datetime
from decimal import Decimal
from pytz import UTC, timezone as pytz_timezone

from django.core.exceptions import ValidationError

from baserow.contrib.database.export_serialized import DatabaseExportSerializedStructure
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.models import (
    NUMBER_TYPE_INTEGER,
    NUMBER_TYPE_DECIMAL,
    TextField,
    LongTextField,
    URLField,
    NumberField,
    RatingField,
    BooleanField,
    DateField,
    LastModifiedField,
    CreatedOnField,
    LinkRowField,
    EmailField,
    FileField,
    SingleSelectField,
    MultipleSelectField,
    PhoneNumberField,
)

from .helpers import import_airtable_date_type_options, set_select_options_on_field
from .registry import AirtableColumnType


class TextAirtableColumnType(AirtableColumnType):
    type = "text"

    def to_baserow_field(self, raw_airtable_column, timezone):
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
        timezone,
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

    def to_baserow_field(self, raw_airtable_column, timezone):
        return LongTextField()


class RichTextTextAirtableColumnType(AirtableColumnType):
    type = "richText"

    def to_baserow_field(self, raw_airtable_column, timezone):
        return LongTextField()

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        timezone,
        files_to_download,
    ):
        # We don't support rich text formatting yet, so this converts the value to
        # plain text.
        return "".join([v["insert"] for v in value["documentValue"]])


class NumberAirtableColumnType(AirtableColumnType):
    type = "number"

    def to_baserow_field(self, raw_airtable_column, timezone):
        type_options = raw_airtable_column.get("typeOptions", {})

        return NumberField(
            number_type=NUMBER_TYPE_DECIMAL
            if type_options.get("format", "integer") == "decimal"
            else NUMBER_TYPE_INTEGER,
            number_decimal_places=max(1, type_options.get("precision", 1)),
            number_negative=type_options.get("negative", True),
        )

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        timezone,
        files_to_download,
    ):
        if value is not None:
            value = Decimal(value)

        if value is not None and not baserow_field.number_negative and value < 0:
            value = None

        return None if value is None else str(value)


class RatingAirtableColumnType(AirtableColumnType):
    type = "rating"

    def to_baserow_field(self, values, timezone):
        return RatingField(max_value=values.get("typeOptions", {}).get("max", 5))


class CheckboxAirtableColumnType(AirtableColumnType):
    type = "checkbox"

    def to_baserow_field(self, raw_airtable_column, timezone):
        return BooleanField()

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        timezone,
        files_to_download,
    ):
        return "true" if value else "false"


class DateAirtableColumnType(AirtableColumnType):
    type = "date"

    def to_baserow_field(self, raw_airtable_column, timezone):
        type_options = raw_airtable_column.get("typeOptions", {})
        return DateField(**import_airtable_date_type_options(type_options))

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        timezone,
        files_to_download,
    ):
        if value is None:
            return value

        # Check if a timezone is provided in the type options, if so, we might want
        # to use that timezone for the conversion later on.
        airtable_timezone = raw_airtable_column.get("typeOptions", {}).get(
            "timeZone", None
        )

        # Baserow doesn't support a "client" option for the date field, so if that is
        # provided, we must fallback on the main timezone chosen during the import.
        # Otherwise, we can use the timezone of that value.
        if airtable_timezone is not None and airtable_timezone != "client":
            timezone = pytz_timezone(airtable_timezone)

        # The provided Airtable date value is always in UTC format. Because Baserow
        # doesn't support different timezones for the date field, we need to convert
        # to the given timezone because then it will be visible in the correct
        # timezone to the user.
        value = (
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
            .astimezone(timezone)
            .replace(tzinfo=UTC)
        )

        if baserow_field.date_include_time:
            return f"{value.isoformat()}"
        else:
            return value.strftime("%Y-%m-%d")


class FormulaAirtableColumnType(AirtableColumnType):
    type = "formula"

    def to_baserow_field(self, raw_airtable_column, timezone):
        type_options = raw_airtable_column.get("typeOptions", {})
        display_type = type_options.get("displayType", "")
        airtable_timezone = type_options.get("timeZone", None)

        # Baserow doesn't support a "client" option for the date field, so if that is
        # provided, we must fallback on the main timezone chosen during the import.
        # Otherwise, we can use the timezone of that field.
        if airtable_timezone is not None and airtable_timezone != "client":
            timezone = pytz_timezone(airtable_timezone)

        # The formula conversion isn't support yet, but because the Created on and
        # Last modified fields work as a formula, we can convert those.
        if display_type == "lastModifiedTime":
            return LastModifiedField(
                timezone=str(timezone),
                **import_airtable_date_type_options(type_options),
            )
        elif display_type == "createdTime":
            return CreatedOnField(
                timezone=str(timezone),
                **import_airtable_date_type_options(type_options),
            )

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        timezone,
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

    def to_baserow_field(self, raw_airtable_column, timezone):
        type_options = raw_airtable_column.get("typeOptions", {})
        return LinkRowField(
            link_row_table_id=type_options.get("foreignTableId"),
            link_row_related_field_id=type_options.get("symmetricColumnId"),
        )

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        timezone,
        files_to_download,
    ):
        foreign_table_id = raw_airtable_column["typeOptions"]["foreignTableId"]
        return [row_id_mapping[foreign_table_id][v["foreignRowId"]] for v in value]


class MultipleAttachmentAirtableColumnType(AirtableColumnType):
    type = "multipleAttachment"

    def to_baserow_field(self, raw_airtable_column, timezone):
        return FileField()

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        timezone,
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

    def to_baserow_field(self, raw_airtable_column, timezone):
        field = SingleSelectField()
        field = set_select_options_on_field(
            field, raw_airtable_column.get("typeOptions", {})
        )
        return field


class MultiSelectAirtableColumnType(AirtableColumnType):
    type = "multiSelect"

    def to_baserow_field(self, raw_airtable_column, timezone):
        field = MultipleSelectField()
        field = set_select_options_on_field(
            field, raw_airtable_column.get("typeOptions", {})
        )
        return field


class PhoneAirtableColumnType(AirtableColumnType):
    type = "phone"

    def to_baserow_field(self, raw_airtable_column, timezone):
        return PhoneNumberField()

    def to_baserow_export_serialized_value(
        self,
        row_id_mapping,
        raw_airtable_column,
        baserow_field,
        value,
        timezone,
        files_to_download,
    ):
        try:
            field_type = field_type_registry.get_by_model(baserow_field)
            field_type.validator(value)
            return value
        except ValidationError:
            return ""
