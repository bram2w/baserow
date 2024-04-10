from django.contrib.auth import get_user_model

from baserow.contrib.builder.elements.operations import ListElementsPageOperationType
from baserow.contrib.builder.workflow_actions.operations import (
    DispatchBuilderWorkflowActionOperationType,
    ListBuilderWorkflowActionsPageOperationType,
)
from baserow.core.registries import PermissionManagerType
from baserow.core.subjects import AnonymousUserSubjectType
from baserow.core.user_sources.subjects import UserSourceUserSubjectType

from .models import Element

User = get_user_model()


class ElementVisibilityPermissionManager(PermissionManagerType):
    """This permission manager handle the element visibility permissions."""

    type = "element_visibility"
    supported_actor_types = [
        UserSourceUserSubjectType.type,
        AnonymousUserSubjectType.type,
    ]

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        """
        If an element is not visible it should be impossible to dispatch an action
        related to this element.
        """

        result = {}

        for check in checks:
            if check.operation_name == DispatchBuilderWorkflowActionOperationType.type:
                if getattr(check.actor, "is_authenticated", False):
                    if (
                        check.context.element.visibility
                        == Element.VISIBILITY_TYPES.NOT_LOGGED
                    ):
                        result[check] = False
                else:
                    if (
                        check.context.element.visibility
                        == Element.VISIBILITY_TYPES.LOGGED_IN
                    ):
                        result[check] = False

        return result

    def filter_queryset(
        self,
        actor,
        operation_name: str,
        queryset,
        workspace=None,
    ):
        """Filters out invisible elements and theirs workflow actions"""

        if operation_name == ListElementsPageOperationType.type:
            if getattr(actor, "is_authenticated", False):
                return queryset.exclude(visibility=Element.VISIBILITY_TYPES.NOT_LOGGED)
            else:
                return queryset.exclude(visibility=Element.VISIBILITY_TYPES.LOGGED_IN)

        elif operation_name == ListBuilderWorkflowActionsPageOperationType.type:
            if getattr(actor, "is_authenticated", False):
                return queryset.exclude(
                    element__visibility=Element.VISIBILITY_TYPES.NOT_LOGGED
                )
            else:
                return queryset.exclude(
                    element__visibility=Element.VISIBILITY_TYPES.LOGGED_IN
                )

        return queryset
