from baserow.api.user.registries import UserDataType

from baserow_premium.license.handler import has_active_premium_license


class PremiumUserDataType(UserDataType):
    type = "premium"

    def get_user_data(self, user, request) -> dict:
        """
        Someone who authenticates via the API should know beforehand if the related
        user has a valid license for the premioum version.
        """

        return {"valid_license": has_active_premium_license(user)}
