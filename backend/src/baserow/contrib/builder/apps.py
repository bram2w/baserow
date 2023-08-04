from django.apps import AppConfig

from baserow.core.registries import object_scope_type_registry, operation_type_registry
from baserow.core.trash.registries import trash_item_type_registry
from baserow.core.usage.registries import workspace_storage_usage_item_registry


class BuilderConfig(AppConfig):
    name = "baserow.contrib.builder"

    def ready(self):
        from baserow.core.registries import application_type_registry

        from .application_types import BuilderApplicationType

        application_type_registry.register(BuilderApplicationType())

        from baserow.contrib.builder.data_sources.object_scopes import (
            BuilderDataSourceObjectScopeType,
        )
        from baserow.contrib.builder.domains.object_scopes import (
            BuilderDomainObjectScopeType,
        )
        from baserow.contrib.builder.elements.object_scopes import (
            BuilderElementObjectScopeType,
        )
        from baserow.contrib.builder.object_scopes import BuilderObjectScopeType
        from baserow.contrib.builder.pages.object_scopes import (
            BuilderPageObjectScopeType,
        )

        object_scope_type_registry.register(BuilderObjectScopeType())
        object_scope_type_registry.register(BuilderPageObjectScopeType())
        object_scope_type_registry.register(BuilderElementObjectScopeType())
        object_scope_type_registry.register(BuilderDomainObjectScopeType())
        object_scope_type_registry.register(BuilderDataSourceObjectScopeType())

        from baserow.contrib.builder.operations import (
            ListDomainsBuilderOperationType,
            ListPagesBuilderOperationType,
            OrderDomainsBuilderOperationType,
            OrderPagesBuilderOperationType,
        )

        operation_type_registry.register(ListPagesBuilderOperationType())
        operation_type_registry.register(OrderPagesBuilderOperationType())
        operation_type_registry.register(ListDomainsBuilderOperationType())
        operation_type_registry.register(OrderDomainsBuilderOperationType())

        from baserow.contrib.builder.elements.usage_types import (
            ImageElementWorkspaceStorageUsageItem,
        )

        workspace_storage_usage_item_registry.register(
            ImageElementWorkspaceStorageUsageItem()
        )

        from baserow.contrib.builder.pages.operations import (
            CreatePageOperationType,
            DeletePageOperationType,
            DuplicatePageOperationType,
            ReadPageOperationType,
            UpdatePageOperationType,
        )

        operation_type_registry.register(CreatePageOperationType())
        operation_type_registry.register(DeletePageOperationType())
        operation_type_registry.register(UpdatePageOperationType())
        operation_type_registry.register(ReadPageOperationType())
        operation_type_registry.register(DuplicatePageOperationType())

        from baserow.contrib.builder.domains.operations import (
            CreateDomainOperationType,
            DeleteDomainOperationType,
            PublishDomainOperationType,
            ReadDomainOperationType,
            RestoreDomainOperationType,
            UpdateDomainOperationType,
        )

        operation_type_registry.register(CreateDomainOperationType())
        operation_type_registry.register(DeleteDomainOperationType())
        operation_type_registry.register(ReadDomainOperationType())
        operation_type_registry.register(UpdateDomainOperationType())
        operation_type_registry.register(PublishDomainOperationType())
        operation_type_registry.register(RestoreDomainOperationType())

        from baserow.contrib.builder.data_sources.operations import (
            CreateDataSourceOperationType,
            DeleteDataSourceOperationType,
            DispatchDataSourceOperationType,
            ListDataSourcesPageOperationType,
            OrderDataSourcesPageOperationType,
            ReadDataSourceOperationType,
            UpdateDataSourceOperationType,
        )

        operation_type_registry.register(CreateDataSourceOperationType())
        operation_type_registry.register(ListDataSourcesPageOperationType())
        operation_type_registry.register(ReadDataSourceOperationType())
        operation_type_registry.register(UpdateDataSourceOperationType())
        operation_type_registry.register(DeleteDataSourceOperationType())
        operation_type_registry.register(OrderDataSourcesPageOperationType())
        operation_type_registry.register(DispatchDataSourceOperationType())

        from baserow.contrib.builder.domains.job_types import PublishDomainJobType
        from baserow.contrib.builder.pages.job_types import DuplicatePageJobType
        from baserow.core.jobs.registries import job_type_registry

        job_type_registry.register(DuplicatePageJobType())
        job_type_registry.register(PublishDomainJobType())

        from baserow.contrib.builder.elements.operations import (
            CreateElementOperationType,
            DeleteElementOperationType,
            ListElementsPageOperationType,
            OrderElementsPageOperationType,
            ReadElementOperationType,
            UpdateElementOperationType,
        )

        operation_type_registry.register(ListElementsPageOperationType())
        operation_type_registry.register(OrderElementsPageOperationType())
        operation_type_registry.register(CreateElementOperationType())
        operation_type_registry.register(ReadElementOperationType())
        operation_type_registry.register(UpdateElementOperationType())
        operation_type_registry.register(DeleteElementOperationType())

        from baserow.core.registries import permission_manager_type_registry

        from .domains.permission_manager import AllowPublicBuilderManagerType

        permission_manager_type_registry.register(AllowPublicBuilderManagerType())

        from .elements.element_types import (
            HeadingElementType,
            ImageElementType,
            InputTextElementType,
            LinkElementType,
            ParagraphElementType,
        )
        from .elements.registries import element_type_registry

        element_type_registry.register(HeadingElementType())
        element_type_registry.register(ParagraphElementType())
        element_type_registry.register(LinkElementType())
        element_type_registry.register(ImageElementType())
        element_type_registry.register(InputTextElementType())

        from .domains.trash_types import DomainTrashableItemType

        trash_item_type_registry.register(DomainTrashableItemType())

        from baserow.contrib.builder.data_providers.registries import (
            builder_data_provider_type_registry,
        )

        from .data_providers.data_provider_types import (
            DataSourceDataProviderType,
            PageParameterDataProviderType,
        )

        builder_data_provider_type_registry.register(DataSourceDataProviderType())
        builder_data_provider_type_registry.register(PageParameterDataProviderType())

        from .domains.receivers import connect_to_domain_pre_delete_signal

        connect_to_domain_pre_delete_signal()

        from .data_sources.receivers import connect_to_data_source_pre_delete_signal

        connect_to_data_source_pre_delete_signal()

        # The signals must always be imported last because they use the registries
        # which need to be filled first.
        import baserow.contrib.builder.ws.signals  # noqa: F403, F401
