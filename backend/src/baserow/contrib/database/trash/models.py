from django.db import models

from baserow.contrib.database.table.models import Table


class TrashedRows(models.Model):
    """
    This model keeps track of rows that had been trashed together in batch.
    """

    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    row_ids = models.JSONField()

    @property
    def trashed(self):
        return True
