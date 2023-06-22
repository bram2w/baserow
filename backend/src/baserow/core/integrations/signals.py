from django.dispatch import Signal

integration_created = Signal()
integration_deleted = Signal()
integration_updated = Signal()
integration_moved = Signal()
integration_orders_recalculated = Signal()
