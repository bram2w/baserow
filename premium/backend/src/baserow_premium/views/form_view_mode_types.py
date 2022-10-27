from baserow_premium.license.handler import LicenseHandler

from baserow.contrib.database.views.registries import FormViewModeType


class FormViewModeTypeSurvey(FormViewModeType):
    type = "survey"

    def before_form_create(self, values: dict, table, user):
        LicenseHandler.raise_if_doesnt_have_premium_features_instance_wide_or_for_group(
            user, table.database.group
        )

    def before_form_update(self, values: dict, view, user):
        # We do want to allow updates of other attributes of the form, like for example
        # changing the name because it's not obvious to the user that's not possible.
        if "mode" in values:
            LicenseHandler.raise_if_doesnt_have_premium_features_instance_wide_or_for_group(
                user, view.table.database.group
            )
