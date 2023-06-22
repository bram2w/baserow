from django.contrib.auth import get_user_model
from django.db import models

from baserow.contrib.database.models import Table
from baserow.core.expression.field import ExpressionField
from baserow.core.integrations.models import Integration
from baserow.core.services.models import Service

User = get_user_model()


class LocalBaserowIntegration(Integration):
    authorized_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)


class LocalBaserowListRows(Service):
    table = models.ForeignKey(
        Table,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )


class LocalBaserowGetRow(Service):
    table = models.ForeignKey(
        Table,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    row_id = ExpressionField()
