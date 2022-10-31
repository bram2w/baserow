from django.contrib.auth import get_user_model
from django.db.models import Q

from baserow_premium.license.features import PREMIUM
from baserow_premium.license.models import License
from baserow_premium.license.registries import LicenseType

from baserow.core.models import GroupUser
from baserow_enterprise.features import RBAC, SSO, TEAMS

User = get_user_model()


class EnterpriseLicenseType(LicenseType):
    type = "enterprise"
    order = 100
    features = [PREMIUM, RBAC, SSO, TEAMS]
    instance_wide = True
    seats_manually_assigned = False

    def get_seats_taken(self, license_object_of_this_type: License) -> int:
        return (
            GroupUser.objects.filter(
                ~Q(permissions="VIEWER"),
                user__profile__to_be_deleted=False,
                user__is_active=True,
            )
            .values("user_id")
            .distinct()
            .count()
        )

    def get_free_users_count(self, license_object_of_this_type: License) -> int:
        total_users = User.objects.filter(
            profile__to_be_deleted=False, is_active=True
        ).count()
        return total_users - self.get_seats_taken(license_object_of_this_type)

    def handle_seat_overflow(self, seats_taken: int, license_object: License):
        # We don't have to do anything because the seat limit is a soft limit.
        pass
