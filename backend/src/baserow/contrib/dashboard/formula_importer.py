import logging

from baserow.contrib.dashboard.data_providers import (
    dashboard_data_provider_type_registry,
)
from baserow.core.exceptions import InstanceTypeDoesNotExist
from baserow.core.formula import (
    BaserowFormula,
    BaserowFormulaException,
    BaserowFormulaObject,
    get_parse_tree_for_formula,
)
from baserow.core.formula.types import BASEROW_FORMULA_MODE_RAW
from baserow.core.services.formula_importer import BaserowFormulaImporter
from baserow.core.utils import to_path

logger = logging.getLogger(__name__)


class DashboardFormulaImporter(BaserowFormulaImporter):
    def get_data_provider_type_registry(self):
        return dashboard_data_provider_type_registry

    def _do_func_import(self, function_argument_expressions, function_name):
        if (
            function_name == "get"
            and function_argument_expressions
            and isinstance(
                function_argument_expressions[0], BaserowFormula.StringLiteralContext
            )
        ):
            argument = function_argument_expressions[0].getText()
            provider, *path = to_path(argument[1:-1])
            if provider == "dashboard_filter":
                dashboard_data_provider_type_registry.get(provider).is_valid(path)
                if int(path[0]) not in self.id_mapping.get("dashboard_filters", {}):
                    # Deleted controls are not exported. Keep their absent value
                    # without retaining a reference to the original dashboard.
                    return "null()"
        return super()._do_func_import(function_argument_expressions, function_name)


def import_formula(formula, id_mapping, **kwargs):
    formula = BaserowFormulaObject.to_formula(formula)
    if formula["mode"] == BASEROW_FORMULA_MODE_RAW or not formula["formula"]:
        return formula
    try:
        tree = get_parse_tree_for_formula(formula["formula"])
        updated = DashboardFormulaImporter(id_mapping, **kwargs).visit(tree)
    except (
        BaserowFormulaException,
        RecursionError,
        InstanceTypeDoesNotExist,
        ValueError,
    ) as exc:
        logger.warning("Skipping the import of an invalid dashboard formula: %s", exc)
        return formula
    return {**formula, "formula": updated}
