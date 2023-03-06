from django.dispatch import Signal

# Note that it could happen that this signal is triggered, but the actual update still
# fails because of a validation error.
before_rows_update = Signal()
before_rows_delete = Signal()

rows_created = Signal()
rows_updated = Signal()
rows_deleted = Signal()

row_orders_recalculated = Signal()
