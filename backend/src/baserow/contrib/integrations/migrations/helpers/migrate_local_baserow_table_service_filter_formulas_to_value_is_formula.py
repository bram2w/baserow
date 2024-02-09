"""
Helpers for 0006_migrate_local_baserow_table_service_filter_formulas_to_value_is_formula
"""

from baserow.core.formula import BaserowFormulaSyntaxError, get_parse_tree_for_formula


def value_parses_as_formula(value: str) -> bool:
    """
    Returns whether the service filter value is a formula or not.
    """

    # If the value is empty, it's not a formula.
    if not value:
        return False

    # If it's a string that's an integer, it's not a formula.
    try:
        int(value)
        return False
    except ValueError:
        pass

    try:
        get_parse_tree_for_formula(value)
        return True
    except BaserowFormulaSyntaxError:
        return False
