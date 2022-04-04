from typing import List

from baserow.contrib.database.fields.dependencies.depedency_rebuilder import (
    rebuild_field_dependencies,
    update_fields_with_broken_references,
    break_dependencies_for_field,
)
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.models import Field


class FieldDependencyHandler:
    @classmethod
    def get_same_table_dependencies(cls, field: Field) -> List[Field]:
        """
        Returns the list of fields that the provided field directly depends on which
        are in the same table.

        :param field: The field to get dependencies for.
        :return: A list of specific field instances.
        """

        return [
            dep.specific
            for dep in field.field_dependencies.filter(table=field.table).all()
        ]

    @classmethod
    def rebuild_dependencies(cls, field, field_cache: FieldCache):
        """
        Rebuilds this fields dependencies based off field_type.get_field_dependencies.

        :param field: The field to rebuild its field dependencies for.
        :param field_cache: A field cache which will be used to lookup fields.
        """

        update_fields_with_broken_references(field)
        rebuild_field_dependencies(field, field_cache)

    @classmethod
    def break_dependencies_delete_dependants(cls, field):
        """
        Breaks any dependant relationships to the field.

        :param field: The field to break all dependant relations onto the field and all
           dependencies
        """

        break_dependencies_for_field(field)
