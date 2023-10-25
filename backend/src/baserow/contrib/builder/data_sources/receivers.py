from django.db.models.signals import pre_delete

from baserow.contrib.builder.data_sources.models import DataSource
from baserow.core.services.handler import ServiceHandler
from baserow.core.services.registries import service_type_registry


def before_data_source_permanently_deleted(sender, instance, **kwargs):
    """
    Delete the service related to a data_source
    """

    if instance.service:
        service_type = service_type_registry.get_by_model(
            instance.service.specific_class
        )
        ServiceHandler().delete_service(service_type, instance.service)


def connect_to_data_source_pre_delete_signal():
    pre_delete.connect(before_data_source_permanently_deleted, DataSource)
