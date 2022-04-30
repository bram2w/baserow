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

view_decoration_created = Signal()
view_decoration_updated = Signal()
view_decoration_deleted = Signal()

view_field_options_updated = Signal()


@receiver(field_signals.field_deleted)
def field_deleted(sender, field, **kwargs):
    if isinstance(field, FileField):
        GalleryView.objects.filter(card_cover_image_field_id=field.id).update(
            card_cover_image_field_id=None
        )

    from baserow.contrib.database.views.registries import (
        decorator_value_provider_type_registry,
    )

    # Call value provider type hooks
    for (
        decorator_value_provider_type
    ) in decorator_value_provider_type_registry.get_all():
        decorator_value_provider_type.after_field_delete(field)
