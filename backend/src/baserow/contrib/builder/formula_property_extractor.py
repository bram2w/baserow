from typing import Dict, List, Set

from django.contrib.auth.models import AbstractUser

from antlr4.tree import Tree

from baserow.contrib.builder.data_providers.registries import (
    builder_data_provider_type_registry,
)
from baserow.contrib.builder.elements.models import Element
from baserow.contrib.builder.formula_importer import BaserowFormulaImporter
from baserow.contrib.builder.pages.models import Page
from baserow.core.formula import BaserowFormula
from baserow.core.formula.exceptions import InvalidBaserowFormula
from baserow.core.utils import merge_dicts_no_duplicates, to_path


class FormulaFieldVisitor(BaserowFormulaImporter):
    """
    This visitor will visit all nodes of a formula and return its formula fields.
    """

    def __init__(self, **kwargs):
        """
        Save the extra context to give it to data provider later.
        """

        self.results = {}
        self.extra_context = kwargs

    def visit(self, tree: Tree) -> Set[str]:
        """
        Due to the way the formula parsing works, the fields that are found by
        visitFunctionCall() need to be collected in an instance variable.

        This method is overridden to create the results set and return it.
        """

        self.results = {}
        super().visit(tree)
        return self.results

    def visitFunctionCall(self, ctx: BaserowFormula.FunctionCallContext):
        """
        Visits all nodes of the formula and stores its Field IDs in the
        self.results instance attribute.
        """

        function_name = ctx.func_name().accept(self).lower()
        function_argument_expressions = ctx.expr()

        parts = [expr.accept(self) for expr in function_argument_expressions]

        if function_name == "get" and isinstance(
            function_argument_expressions[0], BaserowFormula.StringLiteralContext
        ):
            # This is the formula with the function name stripped
            # e.g. "'current_record.field_33'"
            unquoted_arg = parts[0]

            # Remove the surrounding quotes and split the data provider name
            # e.g. "current_record" from the rest of the path, e.g. ["field_33"]
            data_provider_name, *path = to_path(unquoted_arg[1:-1])

            data_provider_type = builder_data_provider_type_registry.get(
                data_provider_name
            )

            try:
                self.results = merge_dicts_no_duplicates(
                    self.results,
                    data_provider_type.extract_properties(path, **self.extra_context),
                )
            except InvalidBaserowFormula:
                # If the property extraction failed because of an Invalid formula
                # we can ignore it. May be the related data source is gone.
                pass


def get_element_field_names(
    elements: List[Element],
    element_map: Dict[str, Element],
) -> Dict[str, Dict[int, List[str]]]:
    """
    Given a list of elements, find its formulas and extract their field names.

    This function will update the results dict. It will only update the
    "external" key, since all builder Elements are user-facing.
    """

    results = {}

    for element in elements:
        results = merge_dicts_no_duplicates(
            results,
            element.get_type().extract_formula_properties(
                element.specific, element_map
            ),
        )

    return {"external": results}


def get_workflow_action_field_names(
    user: AbstractUser,
    page: Page,
    element_map: Dict[str, Element],
) -> Dict[str, Dict[int, List[str]]]:
    """
    Given a Page, loop through all of its workflow actions and find its formula
    field names.

    This function will update the results dict. It will update both the
    "internal" and "external" keys.
        - "internal" field names are those that are only needed by the backend.
        - "external" field names are those needed in the frontend.
    """

    from baserow.contrib.builder.workflow_actions.service import (
        BuilderWorkflowActionService,
    )
    from baserow.contrib.builder.workflow_actions.workflow_action_types import (
        BuilderWorkflowServiceActionType,
    )

    results = {"internal": {}, "external": {}}

    for workflow_action in BuilderWorkflowActionService().get_workflow_actions(
        user, page
    ):
        found_fields = workflow_action.get_type().extract_formula_properties(
            workflow_action, element_map
        )

        if isinstance(workflow_action.get_type(), BuilderWorkflowServiceActionType):
            # Action using service are internal use only
            results["internal"] = merge_dicts_no_duplicates(
                results["internal"], found_fields
            )
        else:
            results["external"] = merge_dicts_no_duplicates(
                results["external"], found_fields
            )

    return results


def get_data_source_field_names(
    page: Page,
) -> Dict[str, Dict[int, List[str]]]:
    """
    Given a Page, loop through all of its data sources. Find all related
    services and return the field names of their formulas.

    This function will update the results dict. It will only update the
    "internal" keys, since data source field names are only required by
    the backend..
    """

    results = {}

    from baserow.contrib.builder.data_sources.handler import DataSourceHandler

    for data_source in DataSourceHandler().get_data_sources_with_cache(page):
        results = merge_dicts_no_duplicates(
            results,
            data_source.extract_formula_properties(data_source),
        )

    return {"internal": results}


def get_formula_field_names(
    user: AbstractUser, page: Page
) -> Dict[str, Dict[int, List[str]]]:
    """
    Given a User and a Page, return all formula field names used in the Page.

    This involves looping over all Elements, Workflow Actions, and Data Sources
    in the Page.

    The field names are categorized by "internal" and "external" field names.

    Internal field names are those formula field names that the frontend does
    not require. By excluding these field names, we improve the security of
    the AB.

    External field names are those formula field names used explicitly by
    Elements or certain Workflow Actions in the Page.

    If the user isn't allowed to view any Elements due to permissions, or
    if the Elements have no formulas, no field names will be returned.
    """

    from baserow.contrib.builder.elements.service import ElementService

    elements = list(ElementService().get_elements(user, page))
    element_map = {e.id: e for e in elements}

    element_results = get_element_field_names(elements, element_map)
    wa_results = get_workflow_action_field_names(user, page, element_map)
    ds_results = get_data_source_field_names(page)

    results = {
        "internal": merge_dicts_no_duplicates(
            wa_results["internal"], ds_results["internal"]
        ),
        "external": merge_dicts_no_duplicates(
            wa_results["external"], element_results["external"]
        ),
    }

    all_field_names = merge_dicts_no_duplicates(
        results["internal"],
        results["external"],
    )
    results["all"] = {key: sorted(value) for key, value in all_field_names.items()}
    results["internal"] = {
        key: sorted(value) for key, value in results["internal"].items()
    }
    results["external"] = {
        key: sorted(value) for key, value in results["external"].items()
    }

    return results
