from abc import ABC
from typing import Dict

from baserow.core.registry import (
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    Instance,
    ModelInstanceMixin,
    ModelRegistryMixin,
    Registry,
)


class DomainType(Instance, ModelInstanceMixin, CustomFieldsInstanceMixin, ABC):
    def prepare_values(self, values: Dict) -> Dict:
        """
        Called before a domain is saved/updates to validate the data or transform the
        data before it is being saved.
        :param values: The values that are about to be saved
        :return: The values after validation/transformation
        """

        return values


class DomainTypeRegistry(Registry, ModelRegistryMixin, CustomFieldsRegistryMixin):
    """
    Contains all the registered domain types.
    """

    name = "domain_type"


domain_type_registry = DomainTypeRegistry()
