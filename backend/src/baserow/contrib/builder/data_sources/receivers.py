from django.db.models.signals import pre_delete

from baserow.contrib.builder.data_sources.models import DataSource
from baserow.core.services.handler import ServiceHandler


def before_data_source_permanently_deleted(sender, instance, **kwargs):
    """
    Delete the service related to a data_source
    """

    if instance.service:
        ServiceHandler().delete_service(instance.service)


def connect_to_data_source_pre_delete_signal():
    pre_delete.connect(before_data_source_permanently_deleted, DataSource)
