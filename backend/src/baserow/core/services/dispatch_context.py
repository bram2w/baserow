from abc import ABC, abstractmethod
from typing import Optional

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
