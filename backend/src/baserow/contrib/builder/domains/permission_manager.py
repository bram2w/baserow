from django.contrib.auth import get_user_model

from baserow.contrib.builder.elements.operations import ListElementsPageOperationType
from baserow.contrib.builder.models import Builder
from baserow.core.operations import ReadApplicationOperationType
from baserow.core.registries import PermissionManagerType, operation_type_registry
from baserow.core.subjects import AnonymousUserSubjectType, UserSubjectType

from .models import Domain

User = get_user_model()


class AllowPublicBuilderManagerType(PermissionManagerType):
    """
    Allow read operations on public builders for all users even anonymous.
    """

    type = "allow_public_builder"
    supported_actor_types = [UserSubjectType.type, AnonymousUserSubjectType.type]

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        result = {}
        for check in checks:
            operation_type = operation_type_registry.get(check.operation_name)
            if operation_type.type == ListElementsPageOperationType.type:
                builder = check.context.builder
            elif (
                operation_type.type == ReadApplicationOperationType.type
                and isinstance(check.context.specific, Builder)
            ):
                builder = check.context.specific
            else:
                continue

            if (
                builder.workspace is None
                and Domain.objects.filter(published_to=builder).exists()
            ):
                # it's a public builder, we allow it.
                result[check] = True

        return result

    def get_permissions_object(self, actor, workspace=None):
        return None
