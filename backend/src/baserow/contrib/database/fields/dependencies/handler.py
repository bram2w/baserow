from typing import Iterable, List, Optional, Tuple

from django.contrib.auth.models import AbstractUser
from django.db.models import Q

from baserow.contrib.database.fields.dependencies.dependency_rebuilder import (
    break_dependencies_for_field,
    rebuild_field_dependencies,
    update_fields_with_broken_references,
)
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.models import Field, LinkRowField
from baserow.contrib.database.fields.registries import FieldType, field_type_registry
from baserow.core.handler import CoreHandler
from baserow.core.models import Workspace
from baserow.core.types import PermissionCheck

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
    def rebuild_dependencies(
        cls, field, field_cache: FieldCache
    ) -> List[FieldDependency]:
        """
        Rebuilds this fields dependencies based off field_type.get_field_dependencies.

        :param field: The field to rebuild its field dependencies for.
        :param field_cache: A field cache which will be used to lookup fields.
        :return: Any new dependencies created by the rebuild.
        """

        update_fields_with_broken_references(field)
        return rebuild_field_dependencies(field, field_cache)

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

    @classmethod
    def rebuild_or_raise_if_user_doesnt_have_permissions_after(
        cls,
        workspace: Workspace,
        user: AbstractUser,
        field: Field,
        field_cache: FieldCache,
        field_operation_name: str,
    ):
        new_dependencies = FieldDependencyHandler.rebuild_dependencies(
            field, field_cache
        )
        FieldDependencyHandler.raise_if_user_doesnt_have_operation_on_dependencies_in_other_tables(
            workspace, user, field, new_dependencies, field_operation_name
        )

    @classmethod
    def raise_if_user_doesnt_have_operation_on_dependencies_in_other_tables(
        cls,
        workspace: Workspace,
        user: AbstractUser,
        field: Field,
        dependencies: List[FieldDependency],
        field_operation_name: str,
    ):
        """
        For a list of dependencies checks the provided user has the provided operation
        on each of the dependency fields raising if they do not. It skips any
        dependencies that point at the same table assuming the user already has rights
        on fields in the table `field` is in.

        :param workspace: The workspace.
        :param user: The user.
        :param field: The field.
        :param dependencies: The dependencies.
        :param field_operation_name: The field operation name.
        """

        perm_checks = []
        for dep in dependencies:
            dependency_field = dep.dependency
            if dependency_field.table_id != field.table_id:
                perm_checks.append(
                    PermissionCheck(
                        actor=user,
                        operation_name=field_operation_name,
                        context=dependency_field,
                    )
                )

        changed_field_type = field_type_registry.get_by_model(field)
        for (
            check,
            result,
        ) in (
            CoreHandler().check_multiple_permissions(perm_checks, workspace).items()
        ):
            if not result:
                raise changed_field_type.get_permission_error_when_user_changes_field_to_depend_on_forbidden_field(
                    check.actor, field, check.context
                )
