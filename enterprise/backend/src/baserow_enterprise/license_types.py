from baserow_enterprise.features import RBAC, SSO
from baserow_premium.license.features import PREMIUM
from baserow_premium.license.registries import LicenseType


class EnterpriseLicenseType(LicenseType):
    type = "enterprise"
    order = 100
    features = [PREMIUM, RBAC, SSO]
    instance_wide = True
