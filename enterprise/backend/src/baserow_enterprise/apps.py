from django.apps import AppConfig


class BaserowEnterpriseConfig(AppConfig):
    name = "baserow_enterprise"

    def ready(self):
        from baserow_enterprise.license_types import EnterpriseLicenseType
        from baserow_premium.license.registries import license_type_registry

        license_type_registry.register(EnterpriseLicenseType())
