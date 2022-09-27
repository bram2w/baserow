import abc
from typing import Any, Dict, List, Union

from django.contrib.auth.models import AbstractUser

from baserow.core.registry import Instance, Registry


class LicenseType(abc.ABC, Instance):
    """
    A type of license that a user can install into Baserow to unlock extra
    functionality. This interface provides the ability for different types of licenses
    to have different behaviour by implementing the various hook methods differently.
    """

    @abc.abstractmethod
    def has_global_prem_or_specific_groups(
        self,
        user: AbstractUser,
    ) -> Union[bool, List[Dict[str, Any]]]:
        """
        Check for which groups the user has an active license. If `True` is returned it
        means that the user has premium access to everything. If an object is returned,
        it means that the user only has access to the specific groups in the returned
        list of dictionaries.

        Example group list return value:

        [
          {
            "type": "group",
            "id": 1,
          },
          {
            "type": "group",
            "id": 2,
          }
        ]

        :param user: The user for whom must be checked if it has an active license.
        :return: To which groups the user has an active premium license for or a
            boolean indicating global premium access instead.
        """

        pass


class LicenseTypeRegistry(Registry[LicenseType]):
    name = "license_type"


license_type_registry: LicenseTypeRegistry = LicenseTypeRegistry()
