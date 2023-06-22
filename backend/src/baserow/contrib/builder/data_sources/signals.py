from django.dispatch import Signal

data_source_created = Signal()
data_source_deleted = Signal()
data_source_updated = Signal()
data_source_moved = Signal()
data_source_orders_recalculated = Signal()
