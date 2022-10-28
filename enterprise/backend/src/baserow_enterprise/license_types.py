from baserow_premium.license.features import PREMIUM
from baserow_premium.license.registries import LicenseType

from baserow_enterprise.features import RBAC, SSO, TEAMS


class EnterpriseLicenseType(LicenseType):
    type = "enterprise"
    order = 100
    features = [PREMIUM, RBAC, SSO, TEAMS]
    instance_wide = True
