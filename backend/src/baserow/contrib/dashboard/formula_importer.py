import logging

from baserow.contrib.dashboard.data_providers import (
    dashboard_data_provider_type_registry,
)
from baserow.core.exceptions import InstanceTypeDoesNotExist
from baserow.core.formula import (
    BaserowFormulaException,
    BaserowFormulaObject,
    get_parse_tree_for_formula,
)
from baserow.core.formula.types import BASEROW_FORMULA_MODE_RAW
from baserow.core.services.formula_importer import BaserowFormulaImporter

logger = logging.getLogger(__name__)


class DashboardFormulaImporter(BaserowFormulaImporter):
    def get_data_provider_type_registry(self):
        return dashboard_data_provider_type_registry


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
