from django.dispatch import Signal, receiver

from baserow.contrib.database.fields import signals as field_signals
from baserow.contrib.database.fields.models import FileField

from .models import GalleryView


view_created = Signal()
view_updated = Signal()
view_deleted = Signal()
views_reordered = Signal()

view_filter_created = Signal()
view_filter_updated = Signal()
view_filter_deleted = Signal()

view_sort_created = Signal()
view_sort_updated = Signal()
view_sort_deleted = Signal()
view_field_options_updated = Signal()


@receiver(field_signals.field_deleted)
def field_deleted(sender, field, **kwargs):
    if isinstance(field, FileField):
        GalleryView.objects.filter(card_cover_image_field_id=field.id).update(
            card_cover_image_field_id=None
        )
