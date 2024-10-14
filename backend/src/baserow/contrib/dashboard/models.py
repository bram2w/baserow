from django.db import models

from baserow.core.models import Application

__all__ = [
    "Dashboard",
]


class Dashboard(Application):
    description = models.TextField(blank=True, db_default="")

    def get_parent(self):
        # Parent is the Application here even if it's at the "same" level
        # but it's a more generic type
        return self.application_ptr
