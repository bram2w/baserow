from django.contrib.auth import get_user_model
from django.db import models

from baserow.contrib.database.data_sync.models import DataSync
from baserow.contrib.database.table.models import Table

User = get_user_model()


class LocalBaserowTableDataSync(DataSync):
    source_table = models.ForeignKey(
        Table,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The source table containing the data you would like to get the data "
        "from.",
    )
    authorized_user = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The user on whose behalf the data is synchronized. The user must "
        "have permission to the table.",
    )
