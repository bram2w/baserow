from dataclasses import dataclass
from typing import Tuple

from baserow.core.registries import Instance, Registry


@dataclass
class RegisteredException(Instance):
    exception_class: Exception
    exception_error: Tuple

    @property
    def type(self):
        return self.exception_error[0]


class APIExceptionRegistry(Registry):
    """
    Registry allowing automatic API error resolution based on
    exception types.
    """

    name = "api_exception"


api_exception_registry = APIExceptionRegistry()
