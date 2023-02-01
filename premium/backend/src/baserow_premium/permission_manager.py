from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from baserow_premium.views.models import OWNERSHIP_TYPE_PERSONAL

from baserow.contrib.database.views.operations import ListViewsOperationType
from baserow.core.exceptions import PermissionDenied, PermissionException
from baserow.core.registries import (
    PermissionManagerType,
    object_scope_type_registry,
    operation_type_registry,
)
from baserow.core.subjects import UserSubjectType
from baserow.core.types import PermissionCheck

User = get_user_model()


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    from .models import Group


class ViewOwnershipPermissionManagerType(PermissionManagerType):
    type = "view_ownership"
    supported_actor_types = [UserSubjectType.type]

    def __init__(self):
        view_scope_type = object_scope_type_registry.get("database_view")

        self.operations = [
            op.type
            for op in operation_type_registry.get_all()
            if object_scope_type_registry.scope_type_includes_scope_type(
                view_scope_type, op.context_scope
            )
        ]

        super().__init__()

    def check_multiple_permissions(
        self,
        checks: List[PermissionCheck],
        group: "Group",
        include_trash: bool = False,
    ) -> Dict[PermissionCheck, Union[bool, PermissionException]]:
        """
        check_multiple_permissions() impl for view ownership checks.

        There are other instances that this method cannot check:
        - CreateViewDecorationOperationType is currently implemented via view_created
          signal since the permission system doesn't allow to pass richer context.
        - ListViewsOperationType and ReadViewsOrderOperationType operations invoke
          filter_queryset() method and hence don't need to be checked.
        """

        result_by_check = {}
        for check in checks:
            actor, operation_name, context = check
            if operation_name not in self.operations or not group or not context:
                continue

            premium = LicenseHandler.user_has_feature(PREMIUM, actor, group)

            view_scope_type = object_scope_type_registry.get("database_view")
            view = object_scope_type_registry.get_parent(
                context, at_scope_type=view_scope_type
            )

            if premium:
                if (
                    view.ownership_type == OWNERSHIP_TYPE_PERSONAL
                    and view.created_by_id != actor.id
                ):
                    result_by_check[check] = PermissionDenied(
                        "The user doesn't own this personal view"
                    )
            else:
                if view.ownership_type == OWNERSHIP_TYPE_PERSONAL:
                    result_by_check[check] = PermissionDenied(
                        "The user doesn't have the authorization to see personal views"
                    )

        return result_by_check

    def filter_queryset(
        self,
        actor: "AbstractUser",
        operation_name: str,
        queryset: QuerySet,
        group: Optional["Group"] = None,
        context: Optional[Any] = None,
    ) -> QuerySet:
        """
        filter_queryset() impl for view ownership filtering.

        :param actor: The actor whom we want to filter the queryset for.
            Generally a `User` but can be a Token.
        :param operation: The operation name for which we want to filter the queryset
            for.
        :param group: An optional group into which the operation takes place.
        :param context: An optional context object related to the current operation.
        :return: The queryset potentially filtered.
        """

        if not isinstance(actor, User):
            return queryset

        if operation_name != ListViewsOperationType.type:
            return queryset

        if not group:
            return queryset

        premium = LicenseHandler.user_has_feature(PREMIUM, actor, group)

        if premium:
            return queryset.filter(
                ~Q(ownership_type=OWNERSHIP_TYPE_PERSONAL)
                | (Q(ownership_type=OWNERSHIP_TYPE_PERSONAL) & Q(created_by=actor))
            )
        else:
            return queryset.exclude(ownership_type=OWNERSHIP_TYPE_PERSONAL)
