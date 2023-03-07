from typing import Optional

from django.utils import timezone

from baserow_premium.license.plugin import LicensePlugin
from baserow_premium.plugins import PremiumPlugin

from baserow.core.models import Group
from baserow.core.registries import plugin_registry
from baserow.core.utils import grouper


class PremiumUsageHandler:
    @classmethod
    def calculate_per_group_seats_taken(cls) -> int:
        """
        Calculates the paid number of seats per group for groups with licenses that
        can have seats per specific group.

        :return: The amount of groups that have been updated.
        """

        count, chunk_size = 0, 256

        cached_license_plugin = plugin_registry.get_by_type(
            PremiumPlugin
        ).get_license_plugin(cache_queries=True)

        groups_queryset = cached_license_plugin.get_groups_to_periodically_update_seats_taken_for().iterator(
            chunk_size=chunk_size
        )

        for groups in grouper(chunk_size, groups_queryset):
            now = timezone.now()
            for group in groups:
                group.seats_taken = cls.calculate_seats_taken_for_group(
                    cached_license_plugin, group
                )
                group.seats_taken_updated_at = now

            Group.objects.bulk_update(
                groups,
                ["seats_taken", "seats_taken_updated_at"],
            )
            count += len(groups)

        return count

    @classmethod
    def calculate_seats_taken_for_group(
        cls, license_plugin: LicensePlugin, group: Group
    ) -> Optional[int]:
        """
        Returns the number of users with seats taken
        group cannot have any paid roles then None will be returned.

        :param license_plugin: The license plugin to get usage with.
        :param group: The group to count paid roles per user for.
        :return: The number of users with a paid role or None if users cannot have
            paid roles in this group.
        """

        usage = license_plugin.get_seat_usage_for_group(group)

        if usage:
            return usage.seats_taken
        else:
            return None
