from baserow.core.auth_provider.models import PasswordAuthProviderModel


class AuthProviderFixtures:
    def create_password_provider(self, **kwargs):
        if "enabled" not in kwargs:
            kwargs["enabled"] = True

        return PasswordAuthProviderModel.objects.create(**kwargs)
