from django.dispatch import receiver

from baserow.contrib.database.fields import signals as field_signals
from baserow.contrib.database.fields.models import FileField

from .models import KanbanView


@receiver(field_signals.field_deleted)
def field_deleted(sender, field, **kwargs):
    if isinstance(field, FileField):
        KanbanView.objects.filter(card_cover_image_field_id=field.id).update(
            card_cover_image_field_id=None
        )


__all__ = [
    "field_deleted",
]
