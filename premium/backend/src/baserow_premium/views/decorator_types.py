from baserow.contrib.database.views.registries import DecoratorType
from baserow_premium.license.handler import check_active_premium_license


class PremiumDecoratorType(DecoratorType):
    def before_create_decoration(self, view, user):
        if user:
            check_active_premium_license(user)

    def before_update_decoration(self, view, user):
        if user:
            check_active_premium_license(user)


class LeftBorderColorDecoratorType(PremiumDecoratorType):
    type = "left_border_color"


class BackgroundColorDecoratorType(PremiumDecoratorType):
    type = "background_color"
