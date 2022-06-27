from typing import Tuple
from dataclasses import dataclass
from baserow.core.registries import Instance, Registry


@dataclass
class RegisteredException(Instance):
    exception_class: Exception
    exception_error: Tuple


class APIExceptionRegistry(Registry):
    """
    Registry allowing automatic API error resolution based on
    exception types.
    """

    name = "api_exception"


api_exception_registry = APIExceptionRegistry()
