from django.db.models import Q

from baserow.contrib.database.tokens.models import Token, TokenPermission
from baserow.core.registries import PermissionManagerType

from .constants import OPERATION_TO_TOKEN_MAP


class TokenPermissionManagerType(PermissionManagerType):
    """
    Check the permission of a token.
    """

    type = "token"

    def check_permissions(
        self, actor, operation, group=None, context=None, include_trash=False
    ):

        if not isinstance(actor, Token):
            return None

        if operation not in OPERATION_TO_TOKEN_MAP:
            return False

        table = context
        token = actor

        return TokenPermission.objects.filter(
            Q(database__table=table)
            | Q(table_id=table.id)
            | Q(table__isnull=True, database__isnull=True),
            token=token,
            type=OPERATION_TO_TOKEN_MAP[operation],
        ).exists()
