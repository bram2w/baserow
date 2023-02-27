from abc import ABCMeta

from baserow.core.registries import OperationType


class BuilderOperationType(OperationType, metaclass=ABCMeta):
    context_scope_name = "builder"


class ListPagesBuilderOperationType(BuilderOperationType):
    type = "builder.list_pages"


class OrderPagesBuilderOperationType(BuilderOperationType):
    type = "builder.order_pages"
