from django.core.exceptions import ValidationError

from baserow.contrib.dashboard.data_sources.dispatch_context import (
    DashboardDispatchContext,
)
from baserow.contrib.dashboard.filters.service import DashboardFilterService
from baserow.core.formula import BaserowFormulaException, resolve_formula
from baserow.core.formula.registries import formula_runtime_function_registry
from baserow.core.formula.validator import ensure_array, ensure_string
from baserow.core.services.exceptions import (
    ServiceImproperlyConfiguredDispatchException,
)


class DashboardFilterOptionsService:
    def get_options(
        self,
        user,
        filter_id,
        request,
        *,
        search="",
        after=None,
        limit=50,
        selected=None,
    ):
        configuration = DashboardFilterService().get_filter(user, filter_id)
        context = DashboardDispatchContext(
            request,
            workspace=configuration.dashboard.workspace,
            dashboard=configuration.dashboard,
        )
        try:
            names, option_values = (
                ensure_array(
                    resolve_formula(formula, formula_runtime_function_registry, context)
                )
                for formula in (
                    configuration.formula_name,
                    configuration.formula_value,
                )
            )
            options = [
                {
                    "value": ensure_string(value),
                    "name": ensure_string(names[index])
                    if index < len(names)
                    else ensure_string(value),
                }
                for index, value in enumerate(option_values)
            ]
        except (BaserowFormulaException, ValidationError) as exc:
            raise ServiceImproperlyConfiguredDispatchException(
                "The option formulas could not be resolved."
            ) from exc
        labels = {}
        for option in options:
            if option["value"].strip():
                labels.setdefault(option["value"], option["name"] or option["value"])
        values = [
            value
            for value, label in labels.items()
            if search.casefold() in label.casefold()
            or search.casefold() in value.casefold()
        ]
        if after is not None:
            try:
                values = values[values.index(after) + 1 :]
            except ValueError:
                values = []
        page = values[:limit]
        available = [value for value in (selected or []) if value in labels]
        return {
            "results": page,
            "labels": {value: labels[value] for value in [*page, *available]},
            "next": values[limit - 1] if len(values) > limit else None,
            "available": available,
        }
