from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AnnotatedOrder:
    """
    A simple helper class which holds an annotation dictionary, as well as a Django
    expression to be used in queryset.order().

    This is needed in case a field types "get_order" method needs to return
    an order expression, as well as an annotation on which the order expression depends.
    """

    annotation: Dict[str, Any]
    order: Any
