from baserow_premium.license.features import PREMIUM
from baserow_premium.license.models import License, LicenseUser
from baserow_premium.license.registries import LicenseType


class PremiumLicenseType(LicenseType):
    type = "premium"
    order = 10
    features = [PREMIUM]

    def get_seats_taken(self, obj: License) -> int:
        return (
            obj.seats_taken if hasattr(obj, "seats_taken") else obj.users.all().count()
        )

    def get_free_users_count(self, license_object_of_this_type: License) -> int:
        return 0

    def handle_seat_overflow(self, seats_taken: int, license_object: License):
        # If there are more seats taken than the license allows, we need to
        # remove the active seats that are outside of the limit.
        LicenseUser.objects.filter(
            pk__in=license_object.users.all()
            .order_by("pk")
            .values_list("pk")[license_object.seats : seats_taken]
        ).delete()
