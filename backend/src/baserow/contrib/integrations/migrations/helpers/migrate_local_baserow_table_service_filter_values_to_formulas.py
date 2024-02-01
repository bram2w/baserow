"""
Helpers for 0003_migrate_local_baserow_table_service_filter_values_to_formulas.
"""

from baserow.contrib.database.fields.field_types import (
    AutonumberFieldType,
    CountFieldType,
    DurationFieldType,
    EmailFieldType,
    FileFieldType,
    FormulaFieldType,
    LinkRowFieldType,
    LongTextFieldType,
    MultipleSelectFieldType,
    NumberFieldType,
    PhoneNumberFieldType,
    RatingFieldType,
    RollupFieldType,
    SingleSelectFieldType,
    TextFieldType,
    URLFieldType,
    UUIDFieldType,
)
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.views.view_filters import (
    ContainsNotViewFilterType,
    ContainsViewFilterType,
    ContainsWordViewFilterType,
    EqualViewFilterType,
    FilenameContainsViewFilterType,
    FilesLowerThanViewFilterType,
    HigherThanViewFilterType,
    LengthIsLowerThanViewFilterType,
    LinkRowContainsViewFilterType,
    LinkRowNotContainsViewFilterType,
    LowerThanViewFilterType,
    NotEqualViewFilterType,
)

TEXT_TYPE_FILTERS_TO_MIGRATE = [
    EqualViewFilterType.type,  # used by other field types
    EqualViewFilterType.type,  # used by other field types
    ContainsViewFilterType.type,  # used by other field types
    ContainsNotViewFilterType.type,  # used by other field types
    FilenameContainsViewFilterType.type,
    ContainsWordViewFilterType.type,
    LinkRowContainsViewFilterType.type,
    LinkRowNotContainsViewFilterType.type,
]

NUMBER_TYPE_FILTERS_TO_MIGRATE = [
    EqualViewFilterType.type,  # used by other field types
    NotEqualViewFilterType.type,  # used by other field types
    FilesLowerThanViewFilterType.type,
    ContainsViewFilterType.type,  # used by other field types
    ContainsNotViewFilterType.type,
    LengthIsLowerThanViewFilterType.type,
    HigherThanViewFilterType.type,  # used by other field types
    LowerThanViewFilterType.type,  # used by other field types
]


FIELD_TYPE_FILTERS_TO_MIGRATE = {
    TextFieldType.type: TEXT_TYPE_FILTERS_TO_MIGRATE,
    LongTextFieldType.type: TEXT_TYPE_FILTERS_TO_MIGRATE,
    URLFieldType.type: TEXT_TYPE_FILTERS_TO_MIGRATE,
    LinkRowFieldType.type: TEXT_TYPE_FILTERS_TO_MIGRATE,
    EmailFieldType.type: TEXT_TYPE_FILTERS_TO_MIGRATE,
    FileFieldType.type: TEXT_TYPE_FILTERS_TO_MIGRATE,
    SingleSelectFieldType.type: TEXT_TYPE_FILTERS_TO_MIGRATE,
    MultipleSelectFieldType.type: TEXT_TYPE_FILTERS_TO_MIGRATE,
    UUIDFieldType.type: TEXT_TYPE_FILTERS_TO_MIGRATE,
    NumberFieldType.type: NUMBER_TYPE_FILTERS_TO_MIGRATE,
    RatingFieldType.type: NUMBER_TYPE_FILTERS_TO_MIGRATE,
    DurationFieldType.type: NUMBER_TYPE_FILTERS_TO_MIGRATE,
    PhoneNumberFieldType.type: NUMBER_TYPE_FILTERS_TO_MIGRATE,
    CountFieldType.type: NUMBER_TYPE_FILTERS_TO_MIGRATE,
    RollupFieldType.type: NUMBER_TYPE_FILTERS_TO_MIGRATE,
    AutonumberFieldType.type: NUMBER_TYPE_FILTERS_TO_MIGRATE,
    FormulaFieldType.type: TEXT_TYPE_FILTERS_TO_MIGRATE
    + NUMBER_TYPE_FILTERS_TO_MIGRATE,
}


def reduce_to_filter_types_to_migrate(service_filters):
    reduced_filters = []
    for service_filter in service_filters:
        field_type = field_type_registry.get_by_model(
            service_filter.field.specific_class
        )
        filter_types_to_migrate = FIELD_TYPE_FILTERS_TO_MIGRATE.get(field_type.type, [])
        if service_filter.type in filter_types_to_migrate:
            reduced_filters.append(service_filter)
    return reduced_filters
