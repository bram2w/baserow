from django.dispatch import Signal

before_group_user_deleted = Signal()
before_group_user_updated = Signal()
before_user_deleted = Signal()

before_group_deleted = Signal()

group_created = Signal()
group_updated = Signal()
group_deleted = Signal()
group_restored = Signal()

group_user_added = Signal()
group_user_updated = Signal()
group_user_deleted = Signal()
groups_reordered = Signal()

application_created = Signal()
application_updated = Signal()
application_deleted = Signal()
applications_reordered = Signal()
