from django.db.models import Q

from baserow.contrib.dashboard.data_providers import DashboardFilterDataProviderType
from baserow.contrib.database.fields.field_filters import AnnotatedQ, FilterBuilder
from baserow.contrib.database.views.view_filters import NotViewFilterTypeMixin
from baserow.core.formula import BaserowFormula, get_parse_tree_for_formula
from baserow.core.formula.types import BASEROW_FORMULA_MODE_RAW
from baserow.core.formula.validator import ensure_string
from baserow.core.services.exceptions import (
    ServiceImproperlyConfiguredDispatchException,
)

from .operators import get_text_filter_operators


def unwrap_expression(expression):
    wrappers = (
        BaserowFormula.BracketsContext,
        BaserowFormula.LeftWhitespaceOrCommentsContext,
        BaserowFormula.RightWhitespaceOrCommentsContext,
    )
    while isinstance(expression, wrappers):
        expression = expression.expr()
    return expression


def get_dashboard_filter_path(formula):
    """Only a direct data reference inherits the control's operator.

    Calculated expressions keep their own source condition: an expression can
    combine several controls, whose operators need not agree.
    """

    if formula["mode"] == BASEROW_FORMULA_MODE_RAW or not formula["formula"]:
        return None
    expression = unwrap_expression(
        get_parse_tree_for_formula(formula["formula"]).expr()
    )
    if not (
        isinstance(expression, BaserowFormula.FunctionCallContext)
        and expression.func_name().getText().lower() == "get"
        and len(expression.expr()) == 1
    ):
        return None
    argument = unwrap_expression(expression.expr(0))
    if not isinstance(argument, BaserowFormula.StringLiteralContext):
        return None
    provider, *path = argument.getText()[1:-1].split(".")
    if provider != "dashboard_filter":
        return None
    DashboardFilterDataProviderType().is_valid(path)
    return path


def get_dashboard_filter_q(service_filter, model, context):
    path = get_dashboard_filter_path(service_filter.value)
    if path is None:
        return None

    provider = DashboardFilterDataProviderType()
    configuration = provider.get_configuration(context, path[0])
    if configuration is None:
        return Q()
    value = provider.get_data_chunk(context, path)
    values = value if isinstance(value, list) else [value]
    values = [ensure_string(value) for value in values if value is not None]
    values = [value for value in values if value.strip()]
    if not values:
        return Q()

    field_object = model._field_objects[service_filter.field_id]
    operator = get_text_filter_operators().get(configuration.operator)
    if operator is None or not operator.field_is_compatible(field_object["field"]):
        raise ServiceImproperlyConfiguredDispatchException(
            "The dashboard filter operator is not compatible with this field."
        )

    # Positive operators accept any selected value; negative ones exclude all.
    builder = FilterBuilder(
        filter_type="AND" if isinstance(operator, NotViewFilterTypeMixin) else "OR"
    )
    name = field_object["name"]
    for value in values:
        builder.filter(
            operator.get_filter(
                name, value, model._meta.get_field(name), field_object["field"]
            )
        )
    query, annotations = builder.get_filters_and_annotations()
    return AnnotatedQ(annotations, query)
