from django.apps import AppConfig

from baserow.core.feature_flags import FF_DASHBOARDS, feature_flag_is_enabled


class DashboardConfig(AppConfig):
    name = "baserow.contrib.dashboard"

    def ready(self):
        from baserow.core.registries import application_type_registry

        from .application_types import DashboardApplicationType

        if feature_flag_is_enabled(FF_DASHBOARDS):
            application_type_registry.register(DashboardApplicationType())
