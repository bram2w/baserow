from typing import TYPE_CHECKING, Any, Optional

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from baserow_premium.views.models import OWNERSHIP_TYPE_PERSONAL

from baserow.contrib.database.views.operations import ListViewsOperationType
from baserow.core.exceptions import PermissionDenied
from baserow.core.registries import (
    PermissionManagerType,
    object_scope_type_registry,
    operation_type_registry,
)

User = get_user_model()


if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    from .models import Group


class ViewOwnershipPermissionManagerType(PermissionManagerType):
    type = "view_ownership"

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

    def check_permissions(
        self,
        actor: "AbstractUser",
        operation_name: str,
        group: Optional["Group"] = None,
        context: Optional[Any] = None,
        include_trash: bool = False,
    ) -> Optional[bool]:
        """
        check_permissions() impl for view ownership checks.

        There are other instances that this method cannot check:
        - CreateViewDecorationOperationType is currently implemented via view_created
          signal since the permission system doesn't allow to pass richer context.
        - OrderViewsOperationType is currently implemented via views_reordered signal
          since the permission system doesn't allow to pass richer context.
        - ListViewsOperationType and ReadViewsOrderOperationType operations invoke
          filter_queryset() method and hence don't need to be checked.

        :param actor: The actor who wants to execute the operation. Generally a `User`,
            but can be a `Token`.
        :param operation_name: The operation name the actor wants to execute.
        :param group: The optional group in which  the operation takes place.
        :param context: The optional object affected by the operation. For instance
            if you are updating a `Table` object, the context is this `Table` object.
        :param include_trash: If true then also checks if the given group has been
            trashed instead of raising a DoesNotExist exception.
        :raise PermissionDenied: If the operation is disallowed a PermissionDenied is
            raised.
        :return: `True` if the operation is permitted, None if the permission manager
            can't decide.
        """

        if not isinstance(actor, User):
            return

        if operation_name not in self.operations:
            return

        if not group:
            return

        if not context:
            return

        premium = LicenseHandler.user_has_feature(PREMIUM, actor, group)

        view_scope_type = object_scope_type_registry.get("database_view")
        view = object_scope_type_registry.get_parent(
            context, at_scope_type=view_scope_type
        )

        if premium:
            if (
                view.ownership_type == OWNERSHIP_TYPE_PERSONAL
                and view.created_by != actor
            ):
                raise PermissionDenied()
        else:
            if view.ownership_type == OWNERSHIP_TYPE_PERSONAL:
                raise PermissionDenied()

        return

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
