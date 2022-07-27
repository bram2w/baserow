from baserow.core.models import Snapshot


class SnapshotFixtures:
    def create_snapshot(self, user=None, **kwargs):
        if user is None:
            user = self.create_user()

        if "snapshot_from_application" not in kwargs:
            kwargs["snapshot_from_application"] = self.create_database_application(
                user=user
            )

        if "snapshot_to_application" not in kwargs:
            kwargs["snapshot_to_application"] = self.create_database_application(
                user=user
            )

        if "name" not in kwargs:
            kwargs["name"] = "TestSnapshot"

        if "created_by" not in kwargs:
            kwargs["created_by"] = user

        snapshot = Snapshot.objects.create(**kwargs)
        return snapshot
