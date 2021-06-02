from django.dispatch import Signal


table_created = Signal()
table_updated = Signal()
table_deleted = Signal()
tables_reordered = Signal()
