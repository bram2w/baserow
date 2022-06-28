from typing import Optional, List, Tuple, Iterable

from django.db.models import Q

from baserow.contrib.database.fields.dependencies.depedency_rebuilder import (
    rebuild_field_dependencies,
    update_fields_with_broken_references,
    break_dependencies_for_field,
)
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.models import Field, LinkRowField
from baserow.contrib.database.fields.registries import field_type_registry, FieldType
from .models import FieldDependency

FieldDependants = List[Tuple[Field, FieldType, List[LinkRowField]]]


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
            dep.specific for dep in field.field_dependencies.filter(table=field.table)
        ] + [
            dep.via.specific
            for dep in field.dependencies.filter(via__table=field.table)
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
        table_id: int,
        field_ids: Iterable[int],
        associated_relations_changed: bool,
        field_cache: FieldCache,
        starting_via_path_to_starting_table: Optional[str] = None,
    ) -> FieldDependants:
        """
        Finds the unique dependant fields of the provided field ids efficiently with the
        least amount of queries. These provided field ids must all be for fields in the
        same table.

        :param table_id: The table that the provided field_ids are all part of.
        :param field_ids: The field ids for which we need to find the dependent fields,
            they must all be in the same table as specified by the table_id param.
        :param associated_relations_changed: If true any relations associated
            with any provided field ids will be treated as having changed also and
            dependants on the relations themselves will be additionally returned.
        :param field_cache: A field cache used to find and store the specific object
            of the dependant.
        :param starting_via_path_to_starting_table: The starting of the dependant
            fields.
        :return: A list containing the dependant fields, their field type and the
            path to starting table.
        """

        if not field_ids:
            return []

        dependant_filter = Q(dependency_id__in=field_ids)
        if associated_relations_changed:
            # Any m2m relationships associated with the provided field_ids have changed.
            # So we want to lookup all fields which are dependant via these link row
            # m2m relationships to properly update them also.
            dependant_filter |= (
                Q(via_id__in=field_ids)
                | Q(via__link_row_related_field_id__in=field_ids)
            ) & ~Q(dependant_id__in=field_ids)
        queryset = (
            FieldDependency.objects.filter(dependant_filter)
            .select_related("dependant", "dependency", "via")
            .order_by("id")
        )

        result: FieldDependants = []
        for field_dependency in queryset:
            dependant_field = field_cache.lookup_specific(field_dependency.dependant)
            if dependant_field is None:
                # If somehow the dependant is trashed it will be None. We can't really
                # trigger any updates for it so ignore it.
                continue
            dependant_field_type = field_type_registry.get_by_model(dependant_field)

            # We only want to add via's to the path which are valid joins required to
            # get from the dependant cell to the dependency. The queryset can return
            # dependencies with via's for dependants in the same row, which don't need
            # a join, so we filter those out here.
            if field_dependency.via is not None and (
                field_dependency.dependant.table_id != table_id
                or (
                    field_dependency.dependency
                    and field_dependency.dependency.table_id == table_id
                )
            ):
                via_path_to_starting_table = (
                    starting_via_path_to_starting_table or []
                ) + [field_dependency.via]
            else:
                via_path_to_starting_table = starting_via_path_to_starting_table

            result.append(
                (dependant_field, dependant_field_type, via_path_to_starting_table)
            )
        return result

    @classmethod
    def get_via_dependants_of_link_field(cls, field: "LinkRowField") -> FieldDependants:
        broken_via_dep_filter = Q(via_id=field.id) & ~Q(dependant_id=field.id)

        related_field_id = field.link_row_related_field_id
        if related_field_id:
            # We also have a related link row field, which is about to get deleted due
            # to the type change also. Find all of it's via deps also excluding its self
            # via dependency.
            broken_via_dep_filter |= Q(via_id=related_field_id) & ~Q(
                dependant_id=related_field_id
            )

        dependants = []
        for via_dep in FieldDependency.objects.filter(broken_via_dep_filter):
            dependant_field = via_dep.dependant.specific
            dependant_field_type = field_type_registry.get_by_model(dependant_field)
            field_dep_tuple = (
                dependant_field,
                dependant_field_type,
                # Don't set any via path as the m2m is being deleted due to the
                # type change and won't be usable.
                [],
            )
            dependants.append(field_dep_tuple)
        return dependants
