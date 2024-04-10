from django.http import HttpRequest

from baserow.core.registry import Instance, Registry


class SettingsDataType(Instance):
    """
    The settings data type can be used to inject an additional payload to the API
    settings response. The returned dict of the `get_settings_data` method is added to
    the payload under the key containing the type name.

    Example:

    class TestSettingsDataType(SettingsDataType):
        type = "test"

        def get_settings_data(request):
            return {"test": "value"}

    settings_data_registry.register(TestSettingsDataType())

    Will result into the following response when the authenticates:
    {
      "allow_new_signups": True,
      "allow_signups_via_workspace_invitations": False,
      ...
      "test": {
        "test": "value"
      }
    }
    """

    def get_settings_data(self, request: HttpRequest) -> dict:
        """
        Should return a dict containing the additional data that must be added to the
        response payload of the settings.

        :param request: The http request related to the settings request.
        :type request: Request
        :return: a dict containing the settings data that must be added to the response.
        """

        raise NotImplementedError(
            "The get_settings_data must be implemented and should return a dict."
        )


class SettingsDataRegistry(Registry[SettingsDataType]):
    name = "api_settings_data"

    def get_all_settings_data(self, request: HttpRequest) -> dict:
        """
        Collects the additional settings data of all the registered settings data type
        instances.

        :param request: The http request related to the settings request.
        :type request: Request
        :return: a dict containing all additional settings data payload for all the
            registered instances.
        """

        return {
            key: value.get_settings_data(request)
            for key, value in self.registry.items()
        }


settings_data_registry: SettingsDataRegistry = SettingsDataRegistry()
