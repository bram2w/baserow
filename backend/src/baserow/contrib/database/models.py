from django.db import models

from baserow.core.models import Application


class Database(Application):
    pass


class Table(models.Model):
    group = models.ForeignKey(Database, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
