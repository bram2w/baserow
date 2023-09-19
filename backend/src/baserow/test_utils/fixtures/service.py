from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowGetRow,
    LocalBaserowListRows,
    LocalBaserowTableServiceFilter,
    LocalBaserowTableServiceSort,
)


class ServiceFixtures:
    def create_local_baserow_get_row_service(self, **kwargs):
        service = self.create_service(LocalBaserowGetRow, **kwargs)
        return service

    def create_local_baserow_list_rows_service(self, **kwargs):
        service = self.create_service(LocalBaserowListRows, **kwargs)
        return service

    def create_local_baserow_table_service_filter(self, **kwargs):
        if "type" not in kwargs:
            kwargs["type"] = "equal"
        return LocalBaserowTableServiceFilter.objects.create(**kwargs)

    def create_local_baserow_table_service_sort(self, **kwargs):
        return LocalBaserowTableServiceSort.objects.create(**kwargs)

    def create_service(self, model_class, **kwargs):
        if "integration" not in kwargs:
            integrations_args = kwargs.pop("integration_args", {})
            integration = self.create_local_baserow_integration(**integrations_args)
        else:
            integration = kwargs.pop("integration", None)
            kwargs.pop("integration_args", None)

        service = model_class.objects.create(integration=integration, **kwargs)

        return service
