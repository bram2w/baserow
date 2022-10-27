from baserow_premium.license.features import PREMIUM
from baserow_premium.license.registries import LicenseType


class PremiumLicenseType(LicenseType):
    type = "premium"
    order = 10
    features = [PREMIUM]
