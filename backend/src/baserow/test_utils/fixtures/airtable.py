from baserow.contrib.database.airtable.models import AirtableImportJob


class AirtableFixtures:
    def create_airtable_import_job(self, **kwargs):
        if "user" not in kwargs:
            kwargs["user"] = self.create_user()

        if "workspace" not in kwargs:
            kwargs["workspace"] = self.create_workspace(user=kwargs["user"])

        if "airtable_share_id" not in kwargs:
            kwargs["airtable_share_id"] = "test"

        return AirtableImportJob.objects.create(**kwargs)
