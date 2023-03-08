from typing import Dict, Generator, Optional, Set

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db.models import Q, QuerySet

from baserow_premium.license.exceptions import InvalidLicenseError
from baserow_premium.license.models import License
from baserow_premium.license.registries import LicenseType, SeatUsageSummary

from baserow.core.models import Group

User = get_user_model()


class LicensePlugin:
    """
    A collection of methods used to query for what licenses a user has access to and
    hence which features they can use.
    """

    def __init__(self, cache_queries: bool = False):
        self.cache_queries = cache_queries
        self.queried_licenses_per_user = {}

    def user_has_feature(
        self,
        feature: str,
        user: AbstractUser,
        group: Group,
    ) -> bool:
        """
        Returns if the provided user has a feature enabled for a specific group from
        an active license or if they have that feature enabled instance wide and hence
        also for this group.

        :param feature: A string identifying a particular feature or set of features
            a license can grant a user.
        :param user: The user to check to see if they have a license active granting
            them the feature.
        :param group: The group to check to see if the user has the feature for.
        """

        return self.user_has_feature_instance_wide(feature, user) or (
            self._has_license_feature_only_for_specific_group(feature, user, group)
        )

    def instance_has_feature(
        self,
        feature: str,
    ) -> bool:
        """
        Checks if the Baserow instance has a particular feature granted by an active
        instance wide license.

        :param feature: The feature to check to see if active. Look for features.py
            files for these constant strings to use.
        :return: True if the feature is enabled globally for all users.
        """

        return any(
            feature in license_type.features
            for license_type in self.get_active_instance_wide_license_types(user=None)
        )

    def group_has_feature(self, feature: str, group: Group) -> bool:
        """
        Checks if the Baserow instance has a particular feature granted by an active
        instance wide license.

        :param feature: The feature to check to see if active. Look for features.py
            files for these constant strings to use.
        :param group: The group to get group wide features for.
        :return: True if the feature is enabled globally for all users.
        """

        return self.instance_has_feature(feature) or any(
            feature in license_type.features
            for license_type in self.get_active_group_licenses(group)
        )

    def user_has_feature_instance_wide(self, feature: str, user: AbstractUser) -> bool:
        """
        Returns if the provided user has a feature enabled for the entire site,
        and not only for one specific group from an active license.

        :param feature: A string identifying a particular feature or set of features
            a license can grant a user.
        :param user: The user to check to see if they have a license active granting
            them the feature.
        """

        return any(
            feature in license_type.features
            for license_type in self.get_active_instance_wide_license_types(user)
        )

    def _has_license_feature_only_for_specific_group(
        self, feature: str, user: AbstractUser, group: Group
    ) -> bool:
        """
        Returns if the provided user has a feature enabled for a specific group from
        an active license, but ignoring any instance-wide licenses they might have.

        :param feature: A string identifying a particular feature or set of features
            a license can grant a user.
        :param user: The user to check to see if they have a group level license active
            granting them the feature.
        :param group: The group to check to see if the user has the feature for.
        """

        return any(
            feature in license_type.features
            for license_type in self.get_active_specific_licenses_only_for_group(
                user, group
            )
        )

    def get_active_instance_wide_license_types(
        self, user: Optional[AbstractUser]
    ) -> Generator[LicenseType, None, None]:
        for available_license in self.get_active_instance_wide_licenses(user):
            yield available_license.license_type

    def get_active_instance_wide_licenses(
        self, user: Optional[User]
    ) -> Generator[License, None, None]:
        """
        For the provided user returns the active licenses they have instance wide.
        If no user is provided then returns any licenses that are globally active for
        every single user in the instance.

        :param user: The user to lookup active instance wide licenses for.
        """

        yield from self._get_active_instance_wide_licenses(
            user.id if user is not None else None
        )

    def _get_active_instance_wide_licenses(
        self, user_id: Optional[int]
    ) -> Generator[License, None, None]:
        if self.cache_queries and user_id in self.queried_licenses_per_user:
            available_licenses = self.queried_licenses_per_user[user_id]
        else:
            available_license_q = Q(cached_untrusted_instance_wide=True)
            if user_id is not None:
                available_license_q |= Q(users__user_id__in=[user_id])

            available_licenses = License.objects.filter(available_license_q).distinct()

        for available_license in available_licenses:
            try:
                if available_license.is_active:
                    yield available_license
            except InvalidLicenseError:
                pass

        if self.cache_queries:
            self.queried_licenses_per_user[user_id] = available_licenses

    def get_active_specific_licenses_only_for_group(
        self, user: AbstractUser, group: Group
    ) -> Generator[LicenseType, None, None]:
        """
        Generates all the licenses for a specific group that a user has. Should not
        return any instance-wide licenses the user has.

        Provided as an overridable hook incase querying for only one specific group
        can be optimized. By default just defers to the `get_per_group_licenses`
        function.

        :param user: The user to get active licenses in the group for.
        :param group: The group to check to see any specific active licenses are
            enabled for.
        :return: A generator which produces the license types that the user has enabled
            for the group.
        """

        per_group_licenses = self.get_active_per_group_licenses(user)
        for active_license in per_group_licenses.get(group.id, set()):
            yield active_license

    def get_active_per_group_licenses(
        self, user: AbstractUser
    ) -> Dict[int, Set[LicenseType]]:
        """
        For the provided user returns the active licenses they have active per group.
        Does not take into account any instance wide licenses the user might have and
        only active licenses for specific groups.

        :param user: The user to lookup active per group licenses for.
        """

        return {}

    def get_active_group_licenses(
        self,
        group: Group,
    ) -> Generator[LicenseType, None, None]:
        """
        For the provided group returns which licenses are active.
        """

        return
        yield

    def get_groups_to_periodically_update_seats_taken_for(self) -> QuerySet:
        """
        Should return a queryset of all the groups that should have their seats_taken
        attribute periodically updated by the nightly usage job when enabled.
        """

        return Group.objects.filter(template__isnull=True)

    def get_seat_usage_for_group(self, group: Group) -> Optional[SeatUsageSummary]:
        """
        Returns for the most important (the license type with the highest order) active
        license type on a group the seat usage summary for that group.

        If it doesn't make sense for that license type to have usage at the group level
        None will be returned.
        """

        sorted_licenses = sorted(
            self.get_active_instance_wide_license_types(user=None),
            key=lambda t: t.order,
            reverse=True,
        )
        if sorted_licenses:
            most_relevant_license_type = sorted_licenses[0]
            return most_relevant_license_type.get_seat_usage_summary_for_group(group)
        else:
            return None
