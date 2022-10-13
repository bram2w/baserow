import abc

from baserow.contrib.database.table.operations import DatabaseTableOperationType
from baserow.core.registries import OperationType


class FieldOperationType(OperationType, abc.ABC):
    context_scope_name = "field"


class CreateFieldOperationType(DatabaseTableOperationType):
    type = "database.table.create_field"


class ListFieldsOperationType(DatabaseTableOperationType):
    type = "database.table.list_fields"
    object_scope_name = "database_field"


class ReadFieldOperationType(FieldOperationType):
    type = "database.table.field.read"


class UpdateFieldOperationType(FieldOperationType):
    type = "database.table.field.update"


class DeleteFieldOperationType(FieldOperationType):
    type = "database.table.field.delete"


class RestoreFieldOperationType(FieldOperationType):
    type = "database.table.field.restore"


class DuplicateFieldOperationType(FieldOperationType):
    type = "database.table.field.duplicate"


class ReadAggregationDatabaseTableOperationType(FieldOperationType):
    type = "database.table.field.read_aggregation"
