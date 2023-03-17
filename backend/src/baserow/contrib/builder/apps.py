from django.apps import AppConfig

from baserow.core.registries import object_scope_type_registry, operation_type_registry


class BuilderConfig(AppConfig):
    name = "baserow.contrib.builder"

    def ready(self):
        from baserow.core.registries import application_type_registry

        from .application_types import BuilderApplicationType

        application_type_registry.register(BuilderApplicationType())

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

        from baserow.contrib.builder.operations import (
            ListPagesBuilderOperationType,
            OrderPagesBuilderOperationType,
        )

        operation_type_registry.register(ListPagesBuilderOperationType())
        operation_type_registry.register(OrderPagesBuilderOperationType())

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

        from baserow.contrib.builder.pages.job_types import DuplicatePageJobType
        from baserow.core.jobs.registries import job_type_registry

        job_type_registry.register(DuplicatePageJobType())

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

        from .elements.element_types import HeadingElementType, ParagraphElementType
        from .elements.registries import element_type_registry

        element_type_registry.register(HeadingElementType())
        element_type_registry.register(ParagraphElementType())

        # The signals must always be imported last because they use the registries
        # which need to be filled first.
        import baserow.contrib.builder.ws.signals  # noqa: F403, F401
