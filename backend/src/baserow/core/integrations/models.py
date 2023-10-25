from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.db import models

from baserow.core.mixins import (
    FractionOrderableMixin,
    HierarchicalModelMixin,
    PolymorphicContentTypeMixin,
    TrashableModelMixin,
    WithRegistry,
)

if TYPE_CHECKING:
    from baserow.core.models import Application


def get_default_integration():
    return ContentType.objects.get_for_model(Integration)


class Integration(
    HierarchicalModelMixin,
    PolymorphicContentTypeMixin,
    WithRegistry,
    FractionOrderableMixin,
    TrashableModelMixin,
    models.Model,
):
    """
    Integrations provide a way to configure external services within an application
    like the Application Builder or the Workflow automation tool.

    An integration can be associated with an application and it stores the data
    required to use the corresponding external service. This data may include an API
    key for accessing an external database service, a user account for querying a
    Baserow database, as well as the necessary URL, credentials, and headers for making
    an API call.
    """

    application = models.ForeignKey(
        "core.Application", on_delete=models.CASCADE, related_name="integrations"
    )
    name = models.CharField(max_length=255)
    order = models.DecimalField(
        help_text="Lowest first.",
        max_digits=40,
        decimal_places=20,
        editable=False,
        default=1,
    )
    content_type = models.ForeignKey(
        ContentType,
        related_name="integrations",
        on_delete=models.SET(get_default_integration),
    )

    @staticmethod
    def get_type_registry():
        from .registries import integration_type_registry

        return integration_type_registry

    class Meta:
        ordering = ("order", "id")

    def get_parent(self):
        return self.application

    @property
    def context_data(self):
        from baserow.core.integrations.registries import integration_type_registry

        integration_type = integration_type_registry.get_by_model(self.specific_class)
        return integration_type.get_context_data(self)

    @classmethod
    def get_last_order(cls, application: "Application"):
        """
        Returns the last order for the given application.

        :param application: The application we want the order for.
        :return: The last order.
        """

        queryset = Integration.objects.filter(application=application)
        return cls.get_highest_order_of_queryset(queryset)[0]

    @classmethod
    def get_unique_order_before_integration(cls, before: "Integration"):
        """
        Returns a safe order value before the given integration in the given
        application.

        :param application: The application we want the order for.
        :param before: The integration before which we want the safe order
        :raises CannotCalculateIntermediateOrder: If it's not possible to find an
            intermediate order. The full order of the items must be recalculated in this
            case before calling this method again.
        :return: The order value.
        """

        queryset = Integration.objects.filter(application=before.application)
        return cls.get_unique_orders_before_item(before, queryset)[0]
