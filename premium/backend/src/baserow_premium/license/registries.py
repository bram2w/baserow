import abc
from typing import List

from baserow_premium.license.models import License

from baserow.core.registry import Instance, Registry


class LicenseType(abc.ABC, Instance):
    """
    A type of license that a user can install into Baserow to unlock extra
    functionality. This interface provides the ability for different types of licenses
    to have different behaviour by implementing the various hook methods differently.
    """

    features: List[str] = []
    """
    A list of features that this license type grants.
    """

    order: int
    """The higher the order the more features/more expensive the license is. Out of
    all instance-wide licenses a user might have, the one with the highest order will
    be shown as a badge in the top of the sidebar in the GUI. """

    instance_wide: bool = False
    """
    When true every user in the instance will have this license if it is active
    regardless of if they are added to a seat on the license or not.
    """

    seats_manually_assigned: bool = True

    def has_feature(self, feature: str):
        return feature in self.features

    def get_seats_taken(self, license_object_of_this_type: License) -> int:
        raise NotImplementedError()

    def get_free_users_count(self, license_object_of_this_type: License) -> int:
        raise NotImplementedError()

    def handle_seat_overflow(self, seats_taken: int, license_object: License):
        raise NotImplementedError()


class LicenseTypeRegistry(Registry[LicenseType]):
    name = "license_type"


license_type_registry: LicenseTypeRegistry = LicenseTypeRegistry()
