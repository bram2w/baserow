from django.dispatch import Signal


group_created = Signal()
group_updated = Signal()
group_deleted = Signal()

application_created = Signal()
application_updated = Signal()
application_deleted = Signal()
