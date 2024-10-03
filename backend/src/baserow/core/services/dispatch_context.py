from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from baserow.core.formula.runtime_formula_context import RuntimeFormulaContext
from baserow.core.services.models import Service
from baserow.core.services.types import RuntimeFormulaContextSubClass


class DispatchContext(RuntimeFormulaContext, ABC):
    own_properties = []

    def __init__(self):
        self.cache = {}  # can be used by data providers to save queries
        super().__init__()

    @abstractmethod
    def range(self, service: Service):
        """
        Should return the pagination requested for the given service.

        :params service: The service we want the pagination for.
        """

    @classmethod
    def from_context(
        cls, context: RuntimeFormulaContextSubClass, **kwargs
    ) -> RuntimeFormulaContextSubClass:
        """
        Return a new DispatchContext instance from the given context, without
        losing the original cached data.

        :params context: The context to create a new DispatchContext instance from.
        """

        new_values = {}
        for prop in cls.own_properties:
            new_values[prop] = getattr(context, prop)
        new_values.update(kwargs)

        new_context = cls(**new_values)
        new_context.cache = {**context.cache}

        return new_context

    @abstractmethod
    def search_query(self) -> Optional[str]:
        """
        Responsible for returning the on-demand search query, depending
        on which module the `DispatchContext` is used by.
        """

    @abstractmethod
    def filters(self) -> Optional[str]:
        """
        Responsible for returning the on-demand filters, depending
        on which module the `DispatchContext` is used by.
        """

    @abstractmethod
    def sortings(self) -> Optional[str]:
        """
        Responsible for returning the on-demand sortings, depending
        on which module the `DispatchContext` is used by.
        """

    @property
    @abstractmethod
    def public_formula_fields(self) -> Optional[Dict[str, Dict[int, List[str]]]]:
        """
        Return a Dict where keys are ["all", "external", "internal"] and values
        dicts. The internal dicts' keys are Service IDs and values are a list
        of Data Source field names.

        Returns None if public_formula_fields shouldn't be included in the dispatch
        context. This is mainly to support a feature flag for this new feature.

        The field names are used to improve the security of the backend by
        ensuring only the minimum necessary data is exposed to the frontend.

        It is used to restrict the queryset as well as to discern which Data
        Source fields are external and safe (user facing) vs internal and
        sensitive (required only by the backend).
        """
