class KanbanViewHasNoSingleSelectField(Exception):
    """
    Raised when the kanban does not have a single select option field and one is
    required.
    """


class KanbanViewFieldDoesNotBelongToSameTable(Exception):
    """
    Raised when the provided field does not belong to the same table as the kanban view.
    """
