class DashboardFilterDoesNotExist(Exception):
    """The requested filter is missing or is in the trash."""


class DashboardFilterInvalidBinding(Exception):
    """A binding must reference one compatible field in its widget's source."""
