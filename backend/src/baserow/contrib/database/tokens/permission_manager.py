from collections import defaultdict

from django.db.models import Q

from baserow.contrib.database.tokens.exceptions import NoPermissionToTable
from baserow.contrib.database.tokens.models import TokenPermission
from baserow.contrib.database.tokens.subjects import TokenSubjectType
from baserow.core.registries import PermissionManagerType

from .constants import OPERATION_TO_TOKEN_MAP, TOKEN_TO_OPERATION_MAP


class TokenPermissionManagerType(PermissionManagerType):
    type = "token"
    supported_actor_types = [TokenSubjectType.type]

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        """
        Checks multiple permissions for token.
        """

        token_checks_by_context = defaultdict(list)
        for check in checks:
            if check.operation_name not in OPERATION_TO_TOKEN_MAP:
                continue
            else:
                token_checks_by_context[check.context].append(check)

        permission_by_token = {}

        # NOTE: we do one query per context because it's simpler but we could probably
        # do better. Regarding the way we use tokens for now it should be enough.
        for context, token_checks in token_checks_by_context.items():
            query_parts = Q()
            for check in token_checks:
                query_parts |= Q(
                    token=check.actor, type=OPERATION_TO_TOKEN_MAP[check.operation_name]
                )

            # Query the DB and store allowed operation per token id
            operations_by_token_id = defaultdict(set)
            for token_id, type in TokenPermission.objects.filter(
                query_parts,
                Q(database__table=context)
                | Q(table_id=context.id)
                | Q(table__isnull=True, database__isnull=True),
            ).values_list("token_id", "type"):
                operations_by_token_id[token_id].add(TOKEN_TO_OPERATION_MAP[type])

            for check in checks:
                if (
                    check.actor.id not in operations_by_token_id
                    or check.operation_name
                    not in operations_by_token_id[check.actor.id]
                ):
                    permission_by_token[check] = NoPermissionToTable(
                        f"The provided token does not have "
                        f"{OPERATION_TO_TOKEN_MAP.get(check.operation_name, 'unknown')}"
                        f" permissions to table {check.context.id}."
                    )
                else:
                    permission_by_token[check] = True

        return permission_by_token
