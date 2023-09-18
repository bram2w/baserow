from typing import Dict

from django.conf import settings

from baserow.contrib.builder.domains.exceptions import SubDomainHasInvalidDomainName
from baserow.contrib.builder.domains.models import CustomDomain, SubDomain
from baserow.contrib.builder.domains.registries import DomainType


class CustomDomainType(DomainType):
    type = "custom"
    model_class = CustomDomain


class SubDomainType(DomainType):
    type = "sub_domain"
    model_class = SubDomain

    def prepare_values(self, values: Dict) -> Dict:
        domain_name = values.get("domain_name", None)

        if domain_name is not None:
            self._validate_domain_name(domain_name)

        return values

    def _validate_domain_name(self, domain_name: str):
        """
        Checks if the subdomain uses a domain name that is among the available domain
        names defined in settings.

        :param domain_name: The name that is being proposed
        :raises SubDomainHasInvalidDomainName: If the domain name is not registered
        """

        for domain in settings.BASEROW_BUILDER_DOMAINS:
            if domain_name.endswith(f".{domain}"):
                # The domain suffix is valid
                return

        raise SubDomainHasInvalidDomainName(domain_name)
