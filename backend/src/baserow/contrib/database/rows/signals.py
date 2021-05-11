from django.dispatch import Signal


# Note that it could happen that this signal is triggered, but the actual update still
# fails because of a validation error.
before_row_update = Signal()
before_row_delete = Signal()

row_created = Signal()
row_updated = Signal()
row_deleted = Signal()
