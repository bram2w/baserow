from django.dispatch import Signal

element_created = Signal()
element_deleted = Signal()
element_updated = Signal()
elements_reordered = Signal()
element_orders_recalculated = Signal()
