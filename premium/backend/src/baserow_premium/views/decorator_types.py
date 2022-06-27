from baserow.contrib.database.views.registries import DecoratorType
from baserow_premium.license.handler import check_active_premium_license_for_group


class PremiumDecoratorType(DecoratorType):
    def before_create_decoration(self, view, user):
        if user:
            check_active_premium_license_for_group(user, view.table.database.group)

    def before_update_decoration(self, view_decoration, user):
        if user:
            check_active_premium_license_for_group(
                user, view_decoration.view.table.database.group
            )


class LeftBorderColorDecoratorType(PremiumDecoratorType):
    type = "left_border_color"


class BackgroundColorDecoratorType(PremiumDecoratorType):
    type = "background_color"
