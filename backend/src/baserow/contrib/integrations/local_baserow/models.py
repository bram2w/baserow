from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F, OrderBy

from baserow.contrib.database.fields.field_filters import FILTER_TYPE_AND
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.models import (
    FILTER_TYPES,
    SORT_ORDER_ASC,
    SORT_ORDER_CHOICES,
    View,
)
from baserow.core.formula.field import FormulaField
from baserow.core.integrations.models import Integration
from baserow.core.services.models import (
    SearchableServiceMixin,
    Service,
    ServiceFilter,
    ServiceSort,
)

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
    filter_type = models.CharField(
        max_length=3,
        choices=FILTER_TYPES,
        default=FILTER_TYPE_AND,
        help_text="Indicates whether all the rows should apply to all filters (AND) "
        "or to any filter (OR).",
    )

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


class LocalBaserowTableServiceFilter(ServiceFilter):
    """
    A service filter applicable to a `LocalBaserowTableService` integration service.
    """

    field = models.ForeignKey(
        "database.Field",
        help_text="The database Field, in the LocalBaserowTableService, "
        "which we would like to filter upon.",
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        max_length=48,
        help_text="Indicates how the field's value must be compared to the filter's "
        "value. The filter is always in this order `field` `type` `value` "
        "(example: `field_1` `contains` `Test`).",
    )
    value = models.CharField(
        max_length=255,
        blank=True,
        help_text="The filter value that must be compared to the field's value.",
    )

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"<LocalBaserowTableServiceFilter {self.field} {self.type} {self.value}>"


class LocalBaserowTableServiceSort(ServiceSort):
    """
    A service sort applicable to a `LocalBaserowTableService` integration service.
    """

    field = models.ForeignKey(
        "database.Field",
        help_text="The database Field, in the LocalBaserowTableService service, "
        "which we would like to sort upon.",
        on_delete=models.CASCADE,
    )
    order = models.CharField(
        max_length=4,
        choices=SORT_ORDER_CHOICES,
        help_text="Indicates the sort order direction. ASC (Ascending) is from A to Z "
        "and DESC (Descending) is from Z to A.",
        default=SORT_ORDER_ASC,
    )

    def __repr__(self):
        return f"<LocalBaserowTableServiceSort {self.field} {self.order}>"

    def get_order(self) -> OrderBy:
        """
        Responsible for returning the `OrderBy` object,
        configured based on the `field` and `order` values.
        """

        field_expr = F(self.field.db_column)

        if self.order == SORT_ORDER_ASC:
            field_order_by = field_expr.asc(nulls_first=True)
        else:
            field_order_by = field_expr.desc(nulls_last=True)

        return field_order_by
