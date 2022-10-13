from baserow.contrib.database.table.models import Table
from baserow.core.registries import ObjectScopeType, object_scope_type_registry


class RowPermissionContext:
    """
    This class allow to wrap up a Table and a row in a same object as we don't have
    a specific `Row` model. Used for the permission checking.
    """

    def __init__(self, table, row):
        self.table = table
        self.row = row

    @property
    def id(self):
        return self.row.id


class DatabaseRowObjectScopeType(ObjectScopeType):
    type = "database_row"
    model_class = RowPermissionContext

    def get_parent_scope(self):
        return object_scope_type_registry.get("database_table")

    def get_parent(self, context):
        return context.table

    def get_all_context_objects_in_scope(self, scope):
        scope_type = object_scope_type_registry.get_by_model(scope)
        if scope_type.type == "group":
            return Table.objects.filter(database__group=scope.id)
        if scope_type.type == "database":
            return Table.objects.filter(database=scope.id)
        if scope_type.type == "database_table":
            return [scope]
        return []
