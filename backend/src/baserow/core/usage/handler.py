from django.db.models import OuterRef, PositiveIntegerField, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from baserow.contrib.database.table.models import Table
from baserow.core.models import Group
from baserow.core.usage.registries import group_storage_usage_item_registry
from baserow.core.utils import grouper


class UsageHandler:
    @classmethod
    def calculate_storage_usage(cls) -> int:
        """
        Calculates the storage usage of every group.
        :return: The amount of groups that have been updated.
        """

        # Item types might need to register some plpgsql functions
        # to speedup the calculations.
        for item in group_storage_usage_item_registry.get_all():
            if hasattr(item, "register_plpgsql_functions"):
                item.register_plpgsql_functions()

        count, chunk_size = 0, 256
        groups_queryset = Group.objects.filter(template__isnull=True).iterator(
            chunk_size=chunk_size
        )

        for groups in grouper(chunk_size, groups_queryset):
            now = timezone.now()
            for group in groups:
                usage_in_bytes = 0
                for item in group_storage_usage_item_registry.get_all():
                    usage_in_bytes += item.calculate_storage_usage(group.id)

                group.storage_usage = usage_in_bytes / (1024 * 1024)  # in MB
                group.storage_usage_updated_at = now

            Group.objects.bulk_update(
                groups, ["storage_usage", "storage_usage_updated_at"]
            )
            count += len(groups)

        return count

    @classmethod
    def get_group_row_count_annotation(cls, outer_ref_name: str = "id") -> Coalesce:
        """
        Generates a subquery that can be used to count the row_count on a Group
        QuerySet.

        :param outer_ref_name: The name of the outer ref used to identify the group
            name.
        :return: The generated SubQuery.
        """

        return Coalesce(
            Subquery(
                Table.objects.filter(
                    row_count__isnull=False,
                    database__group_id=OuterRef(outer_ref_name),
                    database__trashed=False,
                )
                .values("database__group_id")
                .annotate(row_count_total=Sum("row_count"))
                .values_list("row_count_total", flat=True),
                output_field=PositiveIntegerField(),
            ),
            0,
        )
