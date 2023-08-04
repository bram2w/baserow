from django.contrib.contenttypes.models import ContentType
from django.db import models

from baserow.core.integrations.models import Integration
from baserow.core.mixins import (
    PolymorphicContentTypeMixin,
    TrashableModelMixin,
    WithRegistry,
)


def get_default_service_service():
    return ContentType.objects.get_for_model(Integration)


class Service(
    PolymorphicContentTypeMixin,
    WithRegistry,
    TrashableModelMixin,
    models.Model,
):
    """
    An integration service represents one of the services provided by a particular
    external integration.
    It is linked to an integration that contains the configuration required to use
    the associated external service.
    An integration service can be associated with an application or with specific
    objects (such as a page for AB or a node for WA), depending on the integration's
    scope.
    """

    integration = models.ForeignKey(
        Integration,
        related_name="services",
        on_delete=models.SET_NULL,
        null=True,
        help_text="The integration used to establish the connection with the service.",
    )

    content_type = models.ForeignKey(
        ContentType,
        related_name="services",
        on_delete=models.SET(get_default_service_service),
    )

    class Meta:
        ordering = ("id",)

    @staticmethod
    def get_type_registry():
        from .registries import service_type_registry

        return service_type_registry
