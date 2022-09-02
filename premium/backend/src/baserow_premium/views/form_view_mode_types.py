from baserow_premium.license.handler import check_active_premium_license_for_group

from baserow.contrib.database.views.registries import FormViewModeType


class FormViewModeTypeSurvey(FormViewModeType):
    type = "survey"

    def before_form_create(self, values: dict, table, user):
        check_active_premium_license_for_group(user, table.database.group)

    def before_form_update(self, values: dict, view, user):
        # We do want to allow updates of other attributes of the form, like for example
        # changing the name because it's not obvious to the user that's not possible.
        if "mode" in values:
            check_active_premium_license_for_group(user, view.table.database.group)
