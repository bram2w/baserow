from baserow.core.models import Application

from .table.models import Table

__all__ = [
    'Table'
]


class Database(Application):
    pass
