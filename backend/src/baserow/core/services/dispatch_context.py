from abc import ABC, abstractmethod

from baserow.core.formula.runtime_formula_context import RuntimeFormulaContext
from baserow.core.services.models import Service


class DispatchContext(RuntimeFormulaContext, ABC):
    def __init__(self):
        self.cache = {}  # can be used by data providers to save queries
        super().__init__()

    @abstractmethod
    def range(self, service: Service):
        """
        Should return the pagination requested for the given service.

        :params service: The service we want the pagination for.
        """
