from django.dispatch import Signal

team_created = Signal()
team_updated = Signal()
team_deleted = Signal()
team_restored = Signal()

team_subject_created = Signal()
team_subject_deleted = Signal()
team_subject_restored = Signal()
