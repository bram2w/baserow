from django.dispatch import Signal


group_created = Signal()
group_updated = Signal()
group_deleted = Signal()
group_restored = Signal()

group_user_updated = Signal()
group_user_deleted = Signal()

application_created = Signal()
application_updated = Signal()
application_deleted = Signal()
applications_reordered = Signal()
