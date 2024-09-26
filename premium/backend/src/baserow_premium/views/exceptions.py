class KanbanViewHasNoSingleSelectField(Exception):
    """
    Raised when the kanban does not have a single select option field and one is
    required.
    """


class KanbanViewFieldDoesNotBelongToSameTable(Exception):
    """
    Raised when the provided field does not belong to the same table as the kanban view.
    """


class CalendarViewHasNoDateField(Exception):
    """
    Raised when the calendar does not have a date field.
    """


class TimelineViewHasInvalidDateSettings(Exception):
    """
    Raised when the timeline does not have a start date field.
    """
