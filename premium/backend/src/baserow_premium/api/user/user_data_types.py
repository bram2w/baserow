from typing import List

from baserow_premium.license.registries import LicenseType

from baserow.api.user.registries import UserDataType
from baserow.core.models import Group
from baserow.core.registries import plugin_registry


class ActiveLicensesDataType(UserDataType):
    type = "active_licenses"

    def get_user_data(self, user, request) -> dict:
        """
        Someone who authenticates via the API should know beforehand if the related
        user has active licenses.
        """

        from baserow_premium.plugins import PremiumPlugin

        license_plugin = plugin_registry.get_by_type(PremiumPlugin).get_license_plugin()

        per_group_licenses = {
            group_id: {license_type.type: True for license_type in license_types}
            for group_id, license_types in license_plugin.get_active_per_group_licenses(
                user
            ).items()
        }
        instance_wide_licenses = {
            license_type.type: True
            for license_type in license_plugin.get_active_instance_wide_license_types(
                user
            )
        }
        return {
            "instance_wide": instance_wide_licenses,
            "per_group": per_group_licenses,
        }

    @classmethod
    def realtime_message_to_disable_instancewide_license(
        cls, license_to_disable: LicenseType
    ):
        """
        The message body for a realtime event of type user_data_updated which will
        disable a instance-wide license a user has.
        """

        return cls.realtime_message_to_update_user_data(
            {cls.type: {"instance_wide": {license_to_disable.type: False}}}
        )

    @classmethod
    def realtime_message_to_enable_instancewide_license(
        cls, license_to_enable: LicenseType
    ):
        """
        The message body for a realtime event of type user_data_updated which will
        enable a instance-wide license a user has.
        """

        return cls.realtime_message_to_update_user_data(
            {cls.type: {"instance_wide": {license_to_enable.type: True}}}
        )

    @classmethod
    def realtime_message_to_disable_group_license(
        cls, group: Group, license_to_disable: LicenseType
    ):
        """
        The message body for a realtime event of type user_data_updated which will
        disable a group license a user has.
        """

        return cls.realtime_message_to_update_user_data(
            {cls.type: {"per_group": {group.id: {license_to_disable.type: False}}}}
        )

    @classmethod
    def realtime_message_to_enable_group_license(
        cls, group: Group, license_to_enable: LicenseType
    ):
        """
        The message body for a realtime event of type user_data_updated which will
        enable a group license a user has.
        """

        return cls.realtime_message_to_update_user_data(
            {cls.type: {"per_group": {group.id: {license_to_enable.type: True}}}}
        )

    @classmethod
    def realtime_message_to_disable_all_licenses_from_group(cls, group: Group):
        """
        The message body for a realtime event of type user_data_updated which will
        disable all licenses the user got directly for a group.
        """

        return cls.realtime_message_to_update_user_data(
            {cls.type: {"per_group": {group.id: False}}}
        )

    @classmethod
    def realtime_message_to_enable_multiple_group_licenses(
        cls, group: Group, licenses_to_enable: List[LicenseType]
    ):
        """
        The message body for a realtime event of type user_data_updated which will
        grant multiple different licenses from a group.
        """

        return cls.realtime_message_to_update_user_data(
            {
                cls.type: {
                    "per_group": {
                        group.id: {
                            active_license.type: True
                            for active_license in licenses_to_enable
                        }
                    }
                }
            }
        )
