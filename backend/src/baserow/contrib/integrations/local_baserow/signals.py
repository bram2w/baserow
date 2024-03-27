from typing import TYPE_CHECKING, Optional

from django.dispatch import receiver

from baserow.contrib.database.fields.signals import field_updated
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowTableServiceFieldMapping,
)

if TYPE_CHECKING:
    from baserow.contrib.database.fields.models import Field


@receiver(field_updated)
def local_baserow_upsert_row_handle_field_update(
    sender, field: "Field", old_field: Optional["Field"] = None, **kwargs
):
    if old_field:
        field_type = field.get_type()
        old_field_type = old_field.get_type()
        # If the field type has changed, and the new field type is read-only,
        # then we'll delete the field mapping, as the value won't be used.
        if (field_type.type != old_field_type.type) and field_type.read_only:
            LocalBaserowTableServiceFieldMapping.objects.filter(field=field).delete()
