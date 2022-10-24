from django.dispatch import receiver

from baserow_enterprise.role.handler import RoleAssignmentHandler
from baserow_enterprise.role.models import Role

from baserow.core.registries import permission_manager_type_registry
from baserow.core.signals import group_user_added


@receiver(group_user_added)
def group_user_added(sender, group_user, user, invitation, **kwargs):
    group = group_user.group

    if not permission_manager_type_registry.get("role").is_enabled(group):
        return

    role = Role.objects.get(uid=invitation.permissions)
    RoleAssignmentHandler().assign_role(user, group, role=role)
