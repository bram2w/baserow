from baserow.core.models import Group
from baserow.core.usage.registries import group_storage_usage_item_registry


class UsageHandler:
    @classmethod
    def calculate_storage_usage(cls) -> int:
        """
        Calculates the storage usage of every group.
        :return: The amount of groups that have been updated.
        """

        i = 0
        for group in Group.objects.filter(template__isnull=True):
            usage_in_bytes = 0
            for item in group_storage_usage_item_registry.get_all():
                usage_in_bytes += item.calculate_storage_usage(group.id)

            # We want to convert to mega bytes here
            # because otherwise we easily run out of
            # the max integer range of postgres
            usage_in_mega_bytes = usage_in_bytes / 1000000

            group.storage_usage = usage_in_mega_bytes
            group.save()
            i += 1

        return i
