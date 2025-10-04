"""
Signals for User Permissions
Sends WebSocket notifications when permissions change
"""
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from baserow.ws.tasks import broadcast_to_users

from .models import UserPermissionRule, UserFieldPermission


@receiver(post_save, sender=UserPermissionRule)
def user_permission_rule_saved(sender, instance, created, **kwargs):
    """
    Broadcast permission changes to affected users via WebSocket
    """
    from .serializers import UserPermissionRuleSerializer
    
    # Notify the user whose permissions changed
    payload = {
        'type': 'user_permission_updated',
        'table_id': instance.table.id,
        'user_id': instance.user.id,
        'rule': UserPermissionRuleSerializer(instance).data,
        'action': 'created' if created else 'updated'
    }
    
    broadcast_to_users.delay(
        [instance.user.id],
        payload,
        getattr(instance, 'web_socket_id', None)
    )
    
    # Notify admins who can manage permissions
    admin_users = UserPermissionRule.objects.filter(
        table=instance.table,
        role='admin',
        is_active=True
    ).exclude(user=instance.user).values_list('user_id', flat=True)
    
    if admin_users:
        broadcast_to_users.delay(
            list(admin_users),
            payload,
            getattr(instance, 'web_socket_id', None)
        )


@receiver(post_delete, sender=UserPermissionRule)
def user_permission_rule_deleted(sender, instance, **kwargs):
    """
    Notify when permission is revoked
    """
    payload = {
        'type': 'user_permission_revoked',
        'table_id': instance.table.id,
        'user_id': instance.user.id,
    }
    
    broadcast_to_users.delay(
        [instance.user.id],
        payload,
        getattr(instance, 'web_socket_id', None)
    )


@receiver(post_save, sender=UserFieldPermission)
def field_permission_changed(sender, instance, created, **kwargs):
    """
    Notify when field visibility changes
    """
    payload = {
        'type': 'user_field_permission_updated',
        'table_id': instance.user_rule.table.id,
        'user_id': instance.user_rule.user.id,
        'field_id': instance.field.id,
        'permission': instance.permission
    }
    
    broadcast_to_users.delay(
        [instance.user_rule.user.id],
        payload,
        getattr(instance, 'web_socket_id', None)
    )
