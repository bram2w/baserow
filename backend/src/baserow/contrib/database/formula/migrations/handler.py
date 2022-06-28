import logging
import traceback
import typing
from typing import Set

from django.db.models import Q, Min, QuerySet
from tqdm import tqdm

from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.formula import (
    FormulaHandler,
)
from baserow.contrib.database.formula.migrations.migrations import (
    NO_FORMULAS,
    ALL_FORMULAS,
    FormulaMigrations,
    FORMULA_MIGRATIONS,
)
from baserow.core.db import LockedAtomicTransaction

if typing.TYPE_CHECKING:
    from baserow.contrib.database.fields.models import Field

logger = logging.getLogger(__name__)


def _recalculate_formula_metadata_dependencies_first_order(
    field: "Field",
    field_cache: FieldCache,
    recalculate_cell_values: bool,
    already_recalculated: Set[int],
):
    """
    Initially follows the field dependency tree recursively from the provided field
    and recalculates all the fields dependencies first before recalculating the provided
    field.

    :param field: The field to recalculate its metadata and/or cell values for.
    :param field_cache: A cache using to stored queried fields.
    :param recalculate_cell_values: Whether to recalculate the cell values of the
        fields also and not just their metadata.
    :param already_recalculated: A set of field ids which have already been recalculated
        which will used to skip recalculating them again if encountered again.
    """

    from baserow.contrib.database.fields.models import FormulaField

    if field.id in already_recalculated:
        return True

    for dep in field.field_dependencies.all():
        _recalculate_formula_metadata_dependencies_first_order(
            dep, field_cache, recalculate_cell_values, already_recalculated
        )

    field = field_cache.lookup_specific(field)

    if isinstance(field, FormulaField):
        field.save(field_cache=field_cache, raise_if_invalid=False)
        if recalculate_cell_values:
            try:
                model = field_cache.get_model(field.table)
                expr = FormulaHandler.baserow_expression_to_update_django_expression(
                    field.cached_typed_internal_expression, model
                )
                model.objects_and_trash.all().update(**{f"{field.db_column}": expr})
            except Exception as e:
                field.mark_as_invalid_and_save(
                    "Failed to recalculate cell values after formula update."
                )
                logger.warning(
                    f"""During formula update change failed to recalculate formula
{field.name} with id {field.id} in {field.table.name} with id {field.table.id} with
formula {field.formula}. Marking the formula as invalid. The error was caused by:
{traceback.format_exception_only(type(e), e)}"""
                )
        already_recalculated.add(field.id)


class FormulaMigrationHandler:
    @classmethod
    def migrate_formulas_to_latest_version(cls):
        """
        Migrates all formulas found in the database to the latest formula version.
        A formula migration is not like a normal database migration. A formula migration
        consists of the following steps:

        1. Find the oldest formula version in the db currently, stored in the
           FormulaField.version column.
        2. Get the list of migrations to get to the latest formula version.
        3. Loop over the list of migrations. Each migration specifies Q filter
           for each of the three "migration operations" that will be performed
           at the end. The Q filter says "to migrate past this version, this
           migration operation must be applied to these formulas".
        4. Now we have 3 querysets of formulas to apply the following operations
           too to actually perform the migration:
            1. Rebuild the formula's field dependencies.
            2. Recalculate the formula's internal attributes: re-type it, transform it,
               save the results onto the FormulaField model.
            3. Recalculate the formula's cell values given its recalculated attributes.
        5. Finally once we've applied the operations above to the relevant formulas we
           update their FormulaField.version column to the latest version.

        We don't perform a normal database migration to do this because:
        A Django migration cannot rely on code outside of it's file which might
        change. The formula code is large and complex, we can't copy it into each
        migration to ensure the migration will always work.

        Instead a formula migration is set of recalculations/updates per formula in the
        db given the current state of the code.
        """

        cls.migrate_formulas(FORMULA_MIGRATIONS)

    @classmethod
    def migrate_formulas(cls, migrations: FormulaMigrations):
        from baserow.contrib.database.fields.models import FormulaField

        def formulas_need_update():
            return FormulaField.objects.filter(
                ~Q(version=migrations[-1].version)
            ).exists()

        if formulas_need_update():
            logger.info(
                "Found formulas that need to be updated due to their version not "
                "matching the current formula version. Waiting to obtain an "
                "exclusive lock on the formula table before proceeding..."
            )
            with LockedAtomicTransaction(FormulaField):
                logger.info("Formula table has been locked. Proceeding to update.")
                # Another process might have gotten the lock first and already done
                # the update so we recheck once we have the lock.
                if formulas_need_update():
                    cls._update_formulas(migrations)
                else:
                    logger.info(
                        "Some other process updated the formulas before this one "
                        "could... Skipping update."
                    )
        else:
            logger.info("All formulas were already upto date, no update required!")

    @classmethod
    def _update_formulas(cls, migrations: FormulaMigrations):
        from baserow.contrib.database.fields.models import FormulaField

        (
            formulas_to_rebuild_dependencies_for,
            formulas_to_recalculate_attributes_and_cell_values_for,
            formulas_to_only_update_attributes_for,
        ) = cls._get_formula_querysets(migrations)

        cls._do_formula_migration_operations(
            formulas_to_rebuild_dependencies_for,
            formulas_to_recalculate_attributes_and_cell_values_for,
            formulas_to_only_update_attributes_for,
        )

        num_updated = FormulaField.objects.update(version=migrations[-1].version)
        logger.info(f"Updated {num_updated} formulas which were out of " f"date.")

    @classmethod
    def _get_formula_querysets(cls, migrations: FormulaMigrations):
        """
        Given a list of migrations, figures out the current version and constructs
        the three querysets of formulas onto which the three different migration
        operations will be run respectively.

        :param migrations: All migrations available.
        """

        from baserow.contrib.database.fields.models import FormulaField

        formulas = FormulaField.objects.all()
        oldest_version_in_db_currently = FormulaField.objects.aggregate(
            min=Min("version")
        )["min"]

        latest_version = migrations.get_latest_version()
        if oldest_version_in_db_currently > latest_version:
            # When downgrading only recalculate the attributes and the graph.
            # Don't bother recalculating the cell values as it's very very slow and
            # only likely to introduce back bugs that were fixed in newer versions.

            attribute_filter = ALL_FORMULAS
            rebuild_dependencies_filter = ALL_FORMULAS
            recalculate_cell_values_filter = NO_FORMULAS
            logger.info(
                f"Downgrading from {oldest_version_in_db_currently} to "
                f"{latest_version} so automatically rebuilding deps and recalculating"
                f" attrs for all formulas, but skipping cell refresh for speed."
            )
        else:
            relevant_migrations = migrations[
                oldest_version_in_db_currently:latest_version
            ]
            attribute_filter = NO_FORMULAS
            rebuild_dependencies_filter = NO_FORMULAS
            recalculate_cell_values_filter = NO_FORMULAS
            for m in relevant_migrations:
                attribute_filter |= m.recalculate_formula_attributes_for
                rebuild_dependencies_filter |= m.recalculate_field_dependencies_for
                recalculate_cell_values_filter |= m.recalculate_cell_values_for

            logger.info(
                f"Upgrading from version {oldest_version_in_db_currently} to "
                f"{latest_version}"
            )
            logger.info(
                f"Rebuilding dependencies for formulas which match"
                f" {rebuild_dependencies_filter}"
            )
            logger.info(
                f"Recalculating attributes for formulas which match {attribute_filter} or "
                f"{recalculate_cell_values_filter}."
            )
            logger.info(
                f"Refreshing cell values for formulas which match "
                f"{recalculate_cell_values_filter}"
            )

        # We will also recalculate the attributes when refreshing cell values,
        # no need to update attributes twice, so we exclude.
        formulas_to_only_update_attributes_for = formulas.filter(
            attribute_filter
        ).exclude(recalculate_cell_values_filter)
        formulas_to_rebuild_dependencies_for = formulas.filter(
            rebuild_dependencies_filter
        )
        formulas_to_recalculate_cell_values_for = formulas.filter(
            recalculate_cell_values_filter
        )
        return (
            formulas_to_rebuild_dependencies_for,
            formulas_to_recalculate_cell_values_for,
            formulas_to_only_update_attributes_for,
        )

    @classmethod
    def _do_formula_migration_operations(
        cls,
        formulas_to_rebuild_dependencies_for: QuerySet,
        formulas_to_both_calc_attrs_and_refresh_cell_values_for: QuerySet,
        formulas_to_only_recalculate_attributes_for: QuerySet,
    ):
        from baserow.contrib.database.fields.dependencies.handler import (
            FieldDependencyHandler,
        )

        field_cache = FieldCache()
        already_recalculated = set()

        # First recalculate all formula dependencies to ensure they are correct and
        # upto date. This is needed because the new version might calculate
        # dependencies differently than the old version.

        # Use tqdm in manual mode as it doesn't work nicely wrapping generators like
        # .iterator()
        with tqdm(
            total=formulas_to_rebuild_dependencies_for.count(),
            desc="Step 1 of 3: recalculating dependencies for formulas.",
        ) as pbar:
            for field in formulas_to_rebuild_dependencies_for.iterator():
                try:
                    FieldDependencyHandler.rebuild_dependencies(field, field_cache)
                except Exception as e:
                    logger.warning(
                        f"Failed to recalculate dependencies for field: "
                        f"{field.name}({field.id}) in {field.table.name}({field.table.id}) "
                        f"with formula {field.formula}. Skipping as we will later mark "
                        f"this formula as invalid when we recalculate its metadata. "
                        f"The error was caused by: "
                        f"{traceback.format_exception_only(type(e), e)}"
                    )
                pbar.update(1)

        # Now the dependency graph is correct we can starting from the dependencies
        # recalculate the formula metadata and cell values across the entire
        # dependency tree.

        with tqdm(
            total=formulas_to_both_calc_attrs_and_refresh_cell_values_for.count(),
            desc="Step 2 of 3: recalculating metadata and cell values for formulas.",
        ) as pbar:
            for (
                field
            ) in formulas_to_both_calc_attrs_and_refresh_cell_values_for.iterator():
                _recalculate_formula_metadata_dependencies_first_order(
                    field,
                    field_cache,
                    recalculate_cell_values=True,
                    already_recalculated=already_recalculated,
                )
                pbar.update(1)

        with tqdm(
            total=formulas_to_only_recalculate_attributes_for.count(),
            desc="Step 3 of 3: recalculating metadata for formulas which don't need "
            "cell refresh.",
        ) as pbar:
            for field in formulas_to_only_recalculate_attributes_for.iterator():
                _recalculate_formula_metadata_dependencies_first_order(
                    field,
                    field_cache,
                    recalculate_cell_values=False,
                    already_recalculated=already_recalculated,
                )
                pbar.update(1)
