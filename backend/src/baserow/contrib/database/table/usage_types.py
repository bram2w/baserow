from django.db import connection
from django.db.models import Sum
from django.db.models.expressions import RawSQL

from baserow.contrib.database.fields.models import FileField
from baserow.contrib.database.models import Table
from baserow.core.usage.registries import GroupStorageUsageItemType, UsageInBytes
from baserow.core.user_files.models import UserFile

FILENAMES_PER_GROUP_PLPGSQL_FUNCTION = """
drop function if exists filenames_per_group(integer);
create or replace function
filenames_per_group(group_id integer) returns table(filename text)
as
$body$
declare
    field record;
    filename text;
begin
for field in execute '{filefields_query}'
loop
    begin
        return query execute 'select split_part(jsonb_array_elements(field_' || field.field_ptr_id || ') ->> ''name'', ''_'', 1) from {database_table_prefix}' || field.table_id;
    exception
        when undefined_table then
            raise notice 'Could not find database_table_%', field.table_id;
        when undefined_column then
            raise notice 'Could not find field_% in {database_table_prefix}%', field.field_ptr_id, field.table_id;
    end;
end loop;
end;
$body$
language plpgsql;
"""


class TableGroupStorageUsageItemType(GroupStorageUsageItemType):
    type = "table"

    def register_plpgsql_functions(self):
        # Using 9999 as placeholder for the group_id function argument
        with connection.cursor() as cursor:
            cursor.execute(
                FILENAMES_PER_GROUP_PLPGSQL_FUNCTION.format(
                    database_table_prefix=Table.USER_TABLE_DATABASE_NAME_PREFIX,
                    filefields_query=str(
                        FileField.objects.filter(
                            table__trashed=False,
                            table__database__trashed=False,
                            table__database__group=9999,
                        )
                        .only("id", "table_id")
                        .query
                    ).replace("9999", "' || group_id || '"),
                ),
            )

    def calculate_storage_usage(self, group_id: int) -> UsageInBytes:
        usage = (
            UserFile.objects.filter(
                unique__in=RawSQL(
                    "select distinct filenames_per_group(%s)", (group_id,)
                )
            )
            .only("size")
            .aggregate(sum=Sum("size"))["sum"]
        )
        return usage or 0
