from django.db.models.fields.json import KeyTextTransform
from django.db.models import Func, F, Sum

from baserow.contrib.database.fields.models import FileField
from baserow.core.usage.registries import GroupStorageUsageItemType, UsageInBytes
from baserow.core.user_files.models import UserFile


class TableGroupStorageUsageItemType(GroupStorageUsageItemType):
    type = "table"

    def calculate_storage_usage(self, group_id: int) -> UsageInBytes:
        file_fields = FileField.objects.select_related("table").filter(
            table__database__group_id=group_id,
            table__database__trashed=False,
        )

        file_fields_by_table = {}
        for file_field in file_fields:
            table_id = file_field.table_id

            if table_id not in file_fields_by_table:
                file_fields_by_table[table_id] = [file_field]
            else:
                file_fields_by_table[table_id].append(file_field)

        uniques = set()
        for table_id in file_fields_by_table:
            fields = file_fields_by_table[table_id]
            table = fields[0].table
            model = table.get_model(
                fields=fields, field_ids=[], add_dependencies=False, use_cache=False
            )

            for field in fields:
                unique_file_names_of_field = (
                    model.objects.values(
                        unique_file_names=KeyTextTransform(
                            "name",
                            Func(F(field.db_column), function="jsonb_array_elements"),
                        )
                    )
                    .distinct()
                    .values_list("unique_file_names", flat=True)
                )
                uniques_extracted = [
                    unique_file_name.split("_")[0]
                    for unique_file_name in unique_file_names_of_field
                ]
                uniques.update(uniques_extracted)

        usage = UserFile.objects.filter(unique__in=uniques).aggregate(sum=Sum("size"))[
            "sum"
        ]

        return usage or 0
