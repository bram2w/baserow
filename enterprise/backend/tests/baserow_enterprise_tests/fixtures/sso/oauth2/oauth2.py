from baserow_enterprise.sso.oauth2.models import (
    FacebookAuthProviderModel,
    GitHubAuthProviderModel,
    GitLabAuthProviderModel,
    GoogleAuthProviderModel,
    OpenIdConnectAuthProviderModel,
)


class OAuth2Fixture:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_oauth_provider(self, type, **kwargs):
        model_mapping = {
            "facebook": FacebookAuthProviderModel,
            "google": GoogleAuthProviderModel,
            "gitlab": GitLabAuthProviderModel,
            "github": GitHubAuthProviderModel,
            "openid_connect": OpenIdConnectAuthProviderModel,
        }

        if "name" not in kwargs:
            kwargs["name"] = self.faker.name()

        if "client_id" not in kwargs:
            kwargs["client_id"] = "clientid"

        if "secret" not in kwargs:
            kwargs["secret"] = "secret"

        if "enabled" not in kwargs:
            kwargs["enabled"] = True

        return model_mapping[type].objects.create(**kwargs)
