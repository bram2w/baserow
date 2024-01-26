from baserow.core.exceptions import InstanceTypeDoesNotExist


class AppAuthenticationProviderTypeDoesNotExist(InstanceTypeDoesNotExist):
    pass


class IncompatibleUserSourceType(Exception):
    """
    Raised if the auth provider is incompatible with the provider user source
    type.
    """

    def __init__(self, user_source_type: str, auth_provider_type: str, *args, **kwargs):
        self.user_source_type = user_source_type
        self.auth_provider_type = auth_provider_type
        super().__init__(
            f"The auth provider type {auth_provider_type} is incompatible "
            f"with the source type {user_source_type}.",
            *args,
            **kwargs,
        )
