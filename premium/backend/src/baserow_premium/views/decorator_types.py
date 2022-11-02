from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler

from baserow.contrib.database.views.registries import DecoratorType


class PremiumDecoratorType(DecoratorType):
    def before_create_decoration(self, view, user):
        if user:
            LicenseHandler.raise_if_user_doesnt_have_feature(
                user, view.table.database.group, PREMIUM
            )

    def before_update_decoration(self, view_decoration, user):
        if user:
            LicenseHandler.raise_if_user_doesnt_have_feature(
                user, view_decoration.view.table.database.group, PREMIUM
            )


class LeftBorderColorDecoratorType(PremiumDecoratorType):
    type = "left_border_color"


class BackgroundColorDecoratorType(PremiumDecoratorType):
    type = "background_color"
