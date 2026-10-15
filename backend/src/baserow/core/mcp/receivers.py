from django.db.models.signals import pre_delete
from django.dispatch import receiver

from baserow.core.signals import workspace_user_deleted
from baserow.core.user.signals import user_password_changed


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


@receiver(user_password_changed)
def revoke_oauth_tokens_on_password_change(sender, user, **kwargs):
    """
    A password change or reset ends the user's browser sessions, so it signs the
    OAuth apps out too. Endpoint keys are left alone.
    """

    from baserow.core.mcp.oauth.tokens import revoke_user_tokens

    revoke_user_tokens(user)
