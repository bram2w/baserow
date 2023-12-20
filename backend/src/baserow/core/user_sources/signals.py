from django.dispatch import Signal

user_source_created = Signal()
user_source_deleted = Signal()
user_source_updated = Signal()
user_source_moved = Signal()
user_source_orders_recalculated = Signal()
