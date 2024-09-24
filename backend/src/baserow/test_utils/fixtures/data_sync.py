from baserow.contrib.database.data_sync.models import ICalCalendarDataSync


class DataSyncFixtures:
    def create_ical_data_sync(self, user=None, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        data_sync = ICalCalendarDataSync.objects.create(**kwargs)
        return data_sync
