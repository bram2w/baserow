import abc
from typing import List

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

    def has_feature(self, feature: str):
        return feature in self.features


class LicenseTypeRegistry(Registry[LicenseType]):
    name = "license_type"


license_type_registry: LicenseTypeRegistry = LicenseTypeRegistry()
