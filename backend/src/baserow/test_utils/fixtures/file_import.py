import json

from django.core.files.base import ContentFile

from baserow.contrib.database.file_import.models import FileImportJob

data = [["test-1"]]


class FileImportFixtures:
    def create_file_import_job(self, **kwargs):
        if "user" not in kwargs:
            kwargs["user"] = self.create_user()

        if "table" not in kwargs:
            column_count = kwargs.pop("column_count", 2)
            columns = [(f"col__{i}", "text") for i in range(column_count)]
            table, _, _ = self.build_table(
                columns=columns,
                rows=[],
                user=kwargs["user"],
            )
            kwargs["table"] = table

        fields = kwargs["table"].field_set.all()

        if "data" not in kwargs:
            data = []
            row_count = kwargs.pop("row_count", 5)
            for index in range(row_count):
                row = []
                for field_index in range(len(fields)):
                    row.append(f"data_{index}_{field_index}")
                data.append(row)
        else:
            data = kwargs["data"]

        data_file = kwargs.get("data_file", ContentFile(json.dumps(data)))

        job = FileImportJob.objects.create(**kwargs)

        job.data_file.save(None, data_file)

        return job
