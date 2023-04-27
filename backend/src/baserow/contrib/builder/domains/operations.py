from abc import ABC

from baserow.contrib.builder.operations import BuilderOperationType


class BuilderDomainOperationType(BuilderOperationType, ABC):
    context_scope_name = "builder_domain"


class CreateDomainOperationType(BuilderOperationType):
    type = "builder.create_domain"


class DeleteDomainOperationType(BuilderDomainOperationType):
    type = "builder.domain.delete"


class UpdateDomainOperationType(BuilderDomainOperationType):
    type = "builder.domain.update"


class ReadDomainOperationType(BuilderDomainOperationType):
    type = "builder.domain.read"


class PublishDomainOperationType(BuilderDomainOperationType):
    type = "builder.domain.publish"


class RestoreDomainOperationType(BuilderDomainOperationType):
    type = "builder.domain.restore"
