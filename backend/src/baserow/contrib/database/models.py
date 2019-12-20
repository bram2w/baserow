from baserow.core.models import Application

from .table.models import Table
from .views.models import View

__all__ = [
    'Database', 'Table', 'View'
]


class Database(Application):
    pass
