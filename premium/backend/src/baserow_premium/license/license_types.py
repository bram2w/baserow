from typing import Any, Dict, List, Union

from django.contrib.auth.models import AbstractUser

from baserow_premium.license.handler import has_active_premium_license
from baserow_premium.license.registries import LicenseType


class PremiumLicenseType(LicenseType):
    type = "premium"

    def has_global_prem_or_specific_groups(
        self, user: AbstractUser
    ) -> Union[bool, List[Dict[str, Any]]]:
        return has_active_premium_license(user)
