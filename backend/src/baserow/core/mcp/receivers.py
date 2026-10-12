from django.db.models.signals import pre_delete
from django.dispatch import receiver

from baserow.core.signals import workspace_user_deleted


@receiver(workspace_user_deleted)
def revoke_mcp_grants_of_removed_workspace_user(sender, workspace_user, **kwargs):
    from baserow.core.mcp.handler import MCPEndpointHandler

    MCPEndpointHandler().revoke_workspace_grants(
        workspace_user.user_id, workspace_user.workspace_id
    )


@receiver(pre_delete, sender="core.MCPEndpoint")
def revoke_tokens_of_deleted_mcp_endpoint(sender, instance, **kwargs):
    """
    Revokes a grant's tokens however it's deleted, including through a cascade
    when its workspace or user is deleted. The tokens only reference the grant in
    their scope, so nothing would delete them otherwise.
    """

    from baserow.core.mcp.oauth.tokens import revoke_endpoint_tokens

    revoke_endpoint_tokens(instance)
