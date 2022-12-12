from baserow.core.auth_provider.models import PasswordAuthProviderModel


class PasswordProviderHandler:
    @classmethod
    def get(cls) -> PasswordAuthProviderModel:
        """
        Returns the password provider

        :return: The one and only password provider.
        """

        obj, created = PasswordAuthProviderModel.objects.get_or_create()
        return obj
