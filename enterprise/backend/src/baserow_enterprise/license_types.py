from baserow_premium.license.features import PREMIUM
from baserow_premium.license.models import License
from baserow_premium.license.registries import LicenseType, SeatUsageSummary

from baserow_enterprise.features import RBAC, SSO, SUPPORT, TEAMS
from baserow_enterprise.role.seat_usage_calculator import (
    RoleBasedSeatUsageSummaryCalculator,
)


class EnterpriseWithoutSupportLicenseType(LicenseType):
    type = "enterprise_without_support"
    order = 100
    features = [PREMIUM, RBAC, SSO, TEAMS]
    instance_wide = True
    seats_manually_assigned = False

    def get_seat_usage_summary(
        self, license_object_of_this_type: License
    ) -> SeatUsageSummary:
        return RoleBasedSeatUsageSummaryCalculator.get_seat_usage_for_entire_instance()

    def handle_seat_overflow(self, seats_taken: int, license_object: License):
        # We don't have to do anything because the seat limit is a soft limit.
        pass


class EnterpriseLicenseType(EnterpriseWithoutSupportLicenseType):
    type = "enterprise"
    features = EnterpriseWithoutSupportLicenseType.features + [SUPPORT]
