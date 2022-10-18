from baserow.core.registries import OperationType


class FieldOperationType(OperationType):
    context_scope_name = "field"


class CreateFieldOperationType(FieldOperationType):
    type = "database.table.field.create"


class ListFieldsOperationType(FieldOperationType):
    type = "database.table.list_fields"
    object_scope_name = "database_fields"


class ReadFieldOperationType(FieldOperationType):
    type = "database.table.field.read"


class UpdateFieldOperationType(FieldOperationType):
    type = "database.table.field.update"


class DeleteFieldOperationType(FieldOperationType):
    type = "database.table.field.delete"


class DuplicateFieldOperationType(FieldOperationType):
    type = "database.table.field.duplicate"


class UpdateFieldOptionsOperationType(FieldOperationType):
    type = "database.table.field.update_options"
