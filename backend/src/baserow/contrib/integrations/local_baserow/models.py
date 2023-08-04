from django.contrib.auth import get_user_model
from django.db import models

from baserow.contrib.database.models import Table
from baserow.core.formula.field import FormulaField
from baserow.core.integrations.models import Integration
from baserow.core.services.models import Service

User = get_user_model()


class LocalBaserowIntegration(Integration):
    """
    An integration for accessing the local baserow instance. Everything which is
    accessible by the associated user can be accessed with this integration.
    """

    authorized_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)


class LocalBaserowListRows(Service):
    """
    A model for the local baserow list rows service configuration data.
    """

    table = models.ForeignKey(
        Table,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )


class LocalBaserowGetRow(Service):
    """
    A model for the local baserow get row service configuration data.
    """

    table = models.ForeignKey(
        Table,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    row_id = FormulaField()
