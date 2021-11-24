from baserow.core.registry import Instance, Registry


class UserDataType(Instance):
    """
    The user data type can be used to inject an additional payload to the API
    JWT response. This is the response when a user authenticates or refreshes his
    token. The returned dict of the `get_user_data` method is added to the payload
    under the key containing the type name.

    Example:

    class TestUserDataType(UserDataType):
        type = "test"

        def get_user_data(user, request):
            return {"test": "value"}

    user_data_registry.register(TestUserDataType())

    Will result into the following response when the user authenticates:
    {
      "token": "eyJ....",
      "user: {
        "id": 1,
        ...
      },
      "test": {
        "test": "value"
      }
    }
    """

    def get_user_data(self, user, request) -> dict:
        """
        Should return a dict containing the additional information that must be added
        to the response payload after the user authenticates.

        :param user: The related user that just authenticated.
        :type user: User
        :param request: The request when the user authenticated.
        :type request: Request
        :return: a dict containing the user data that must be added to the response.
        """

        raise NotImplementedError(
            "The get_user_data must be implemented and should return a dict."
        )


class UserDataRegistry(Registry):
    name = "api_user_data"

    def get_all_user_data(self, user, request) -> dict:
        """
        Collects the additional user data of all the registered user data type
        instances.

        :param user: The user that just authenticated.
        :type user: User
        :param request: The request when the user authenticated.
        :type request: Request
        :return: a dict containing all additional user data payload for all the
            registered instances.
        """

        return {
            key: value.get_user_data(user, request)
            for key, value in self.registry.items()
        }


user_data_registry = UserDataRegistry()
