from django.dispatch import receiver

from baserow.contrib.database.fields.exceptions import CannotDeletePrimaryField
from baserow.contrib.database.fields.signals import before_field_deleted

from .models import DataSyncSyncedProperty


@receiver(before_field_deleted)
def before_field_deleted(
    sender, field_id, field, user, allow_deleting_primary=False, **kwargs
):
    # This typically happens when the table is trashed, and then we do want to allow it.
    if allow_deleting_primary:
        return
    synced_property = DataSyncSyncedProperty.objects.filter(field=field).first()
    # It should not be possible to delete a unique primary field because they're
    # needed for row identification.
    if synced_property and synced_property.unique_primary:
        raise CannotDeletePrimaryField("Can't delete unique primary field.")
