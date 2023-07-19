from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowGetRow,
    LocalBaserowListRows,
)


class ServiceFixtures:
    def create_local_baserow_get_row_service(self, **kwargs):
        service = self.create_service(LocalBaserowGetRow, **kwargs)
        return service

    def create_local_baserow_list_rows_service(self, **kwargs):
        service = self.create_service(LocalBaserowListRows, **kwargs)
        return service

    def create_service(self, model_class, integration=None, **kwargs):
        if not integration:
            integrations_args = kwargs.pop("integration_args", {})
            integration = self.create_local_baserow_integration(**integrations_args)

        service = model_class.objects.create(integration=integration, **kwargs)

        return service
