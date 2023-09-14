from django.contrib.auth import get_user_model
from django.db import models

from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.models import View
from baserow.core.formula.field import FormulaField
from baserow.core.integrations.models import Integration
from baserow.core.services.models import SearchableServiceMixin, Service

User = get_user_model()


class LocalBaserowIntegration(Integration):
    """
    An integration for accessing the local baserow instance. Everything which is
    accessible by the associated user can be accessed with this integration.
    """

    authorized_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)


class LocalBaserowTableService(Service):
    view = models.ForeignKey(View, null=True, default=None, on_delete=models.SET_NULL)
    table = models.ForeignKey(Table, null=True, default=None, on_delete=models.SET_NULL)

    class Meta:
        abstract = True


class LocalBaserowListRows(LocalBaserowTableService, SearchableServiceMixin):
    """
    A model for the local baserow list rows service configuration data.
    """


class LocalBaserowGetRow(LocalBaserowTableService, SearchableServiceMixin):
    """
    A model for the local baserow get row service configuration data.
    """

    row_id = FormulaField()
