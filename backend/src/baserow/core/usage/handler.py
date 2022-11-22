from django.utils import timezone

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
