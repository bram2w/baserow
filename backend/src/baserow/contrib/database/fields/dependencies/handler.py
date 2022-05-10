from typing import Optional, List, Tuple

from baserow.contrib.database.fields.dependencies.depedency_rebuilder import (
    rebuild_field_dependencies,
    update_fields_with_broken_references,
    break_dependencies_for_field,
)
from baserow.contrib.database.fields.registries import field_type_registry, FieldType
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.models import Field

from .models import FieldDependency


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

    @classmethod
    def get_dependant_fields_with_type(
        cls,
        field_ids: list,
        field_cache: FieldCache,
        starting_via_path_to_starting_table: Optional[str] = None,
    ) -> List[Tuple[Field, FieldType, str]]:
        """
        Finds the unique dependant fields of the provided field ids efficiently with the
        least amount of queries.

        :param field_ids: The field ids for which we need to find the dependent fields.
        :param field_cache: A field cache used to find and store the specific object
            of the dependant.
        :param starting_via_path_to_starting_table: The starting of the dependant
            fields.
        :return: A list containing the dependant fields, their field type and the
            path to starting table.
        """

        queryset = (
            FieldDependency.objects.filter(dependency_id__in=field_ids)
            .select_related("dependant")
            .order_by("id")
        )

        result = []
        for field_dependency in queryset:
            dependant_field = field_cache.lookup_specific(field_dependency.dependant)
            if dependant_field is None:
                # If somehow the dependant is trashed it will be None. We can't really
                # trigger any updates for it so ignore it.
                continue
            dependant_field_type = field_type_registry.get_by_model(dependant_field)
            if field_dependency.via is not None:
                via_path_to_starting_table = (
                    starting_via_path_to_starting_table or []
                ) + [field_dependency.via]
            else:
                via_path_to_starting_table = starting_via_path_to_starting_table
            result.append(
                (dependant_field, dependant_field_type, via_path_to_starting_table)
            )
        return result
