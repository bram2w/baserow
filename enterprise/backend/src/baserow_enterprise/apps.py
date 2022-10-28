from django.apps import AppConfig


class BaserowEnterpriseConfig(AppConfig):
    name = "baserow_enterprise"

    def ready(self):
        from baserow_premium.license.registries import license_type_registry

        from baserow_enterprise.license_types import EnterpriseLicenseType

        license_type_registry.register(EnterpriseLicenseType())
        from baserow.core.registries import plugin_registry

        from .plugins import EnterprisePlugin

        plugin_registry.register(EnterprisePlugin())

        from baserow.core.registries import auth_provider_type_registry
        from baserow_enterprise.sso.saml.auth_provider_types import SamlAuthProviderType

        auth_provider_type_registry.register(SamlAuthProviderType())
