from django.dispatch import Signal


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

grid_view_field_options_updated = Signal()
