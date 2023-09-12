from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    name = "baserow.contrib.integrations"

    def ready(self):
        from baserow.contrib.integrations.local_baserow.integration_types import (
            LocalBaserowIntegrationType,
        )
        from baserow.core.integrations.registries import integration_type_registry
        from baserow.core.services.registries import service_type_registry

        integration_type_registry.register(LocalBaserowIntegrationType())

        from baserow.contrib.integrations.local_baserow.service_types import (
            LocalBaserowGetRowUserServiceType,
            LocalBaserowListRowsUserServiceType,
        )

        service_type_registry.register(LocalBaserowGetRowUserServiceType())
        service_type_registry.register(LocalBaserowListRowsUserServiceType())
