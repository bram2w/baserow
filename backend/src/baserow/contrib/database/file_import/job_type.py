import json

from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from baserow.core.utils import grouper
from baserow.core.jobs.registries import JobType
from baserow.contrib.database.table.signals import table_updated

from .models import FileImportJob
from .constants import FILE_IMPORT_IN_PROGRESS


BATCH_SIZE = 1024


class FileImportJobType(JobType):
    type = "file_import"

    model_class = FileImportJob

    max_count = 1

    request_serializer_field_names = []

    request_serializer_field_overrides = {}

    serializer_field_names = [
        "table_id",
    ]

    serializer_field_overrides = {
        "table_id": serializers.IntegerField(
            required=True,
            help_text="Table id where data will be imported.",
        ),
    }

    def prepare_values(self, values, user):
        """
        Filter data from the values dict. Data are going to be added later as a file.
        See `.after_job_creation()`.
        """

        filtered_dict = dict(**values)
        filtered_dict.pop("data")
        return filtered_dict

    def after_job_creation(self, job, values):
        """
        Save the data file for the newly created job.
        """

        data_file = ContentFile(json.dumps(values["data"]))
        job.data_file.save(None, data_file)

    def run(self, job, progress):
        """
        Fills the provided table with the normalized data that needs to be created upon
        creation of the table.
        """

        data = []

        table = job.table

        group = table.database.group
        group.has_user(job.user, raise_error=True)

        model = table.get_model()
        fields = list(table.field_set.all())

        with job.data_file.open("r") as fin:
            data = json.load(fin)

        sub_progress = progress.create_child(100, len(data))

        sub_progress.increment(state=FILE_IMPORT_IN_PROGRESS)

        # We split the import in batch to be able to track the job progress
        for count, chunk in enumerate(grouper(BATCH_SIZE, data)):
            bulk_data = [
                model(
                    order=count * BATCH_SIZE + index + 1,
                    **{
                        f"field_{fields[index].id}": str(value)
                        for index, value in enumerate(row)
                    },
                )
                for index, row in enumerate(chunk)
            ]

            model.objects.bulk_create(bulk_data)

            sub_progress.increment(
                len(chunk),
                state=FILE_IMPORT_IN_PROGRESS,
            )

        def after_commit():
            job.refresh_from_db()
            job.data_file.delete()

        # Remove the file after the commit to save space
        transaction.on_commit(after_commit)

        table_updated.send(self, table=table, user=None, force_table_refresh=True)
