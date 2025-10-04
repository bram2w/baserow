"""
User Permissions Models - Contratos Django
Ubicación: backend/src/baserow/contrib/database/user_permissions/models.py
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.models import View
from baserow.core.mixins import (
    CreatedAndUpdatedOnMixin,
    OrderableMixin,
    TrashableModelMixin,
)

User = get_user_model()


class UserPermissionRule(
    TrashableModelMixin,
    CreatedAndUpdatedOnMixin, 
    OrderableMixin,
    models.Model
):
    """
    Regla de permisos por usuario para una tabla específica.
    Extiende el sistema de permisos existente añadiendo una capa granular por usuario.
    """
    
    class RoleChoices(models.TextChoices):
        ADMIN = "admin", _("Admin")
        MANAGER = "manager", _("Manager") 
        COORDINATOR = "coordinator", _("Coordinator")
        VIEWER = "viewer", _("Viewer")
    
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="user_permission_rules",
        help_text=_("Table to which this permission rule applies")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="permission_rules",
        help_text=_("User to whom this permission rule applies")
    )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.VIEWER,
        help_text=_("Base role defining default permissions level")
    )
    row_filter = models.JSONField(
        default=dict,
        blank=True,
        help_text=_(
            "JSON filter to limit visible rows using user context variables. "
            "Example: {'assigned_to': '{user.id}', 'department': '{user.department}'}"
        )
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this permission rule is currently active")
    )
    
    class Meta:
        app_label = "user_permissions"
        db_table = "database_user_permission_rule"
        unique_together = [["table", "user"]]
        indexes = [
            models.Index(fields=["table", "user"]),
            models.Index(fields=["table", "role"]), 
            models.Index(fields=["user", "is_active"]),
        ]
        
    def __str__(self):
        return f"{self.user.email} - {self.table.name} ({self.role})"
        
    def clean(self):
        """Valida que el usuario tenga acceso al workspace de la tabla"""
        if not self.table.database.workspace.users.filter(id=self.user.id).exists():
            raise ValidationError(
                _("User must be a member of the workspace to have table permissions")
            )
            
    @property
    def role_permissions(self):
        """Retorna permisos base según el rol asignado"""
        role_perms = {
            self.RoleChoices.ADMIN: {
                "can_read": True,
                "can_create": True, 
                "can_update": True,
                "can_delete": True,
                "can_manage_permissions": True,
            },
            self.RoleChoices.MANAGER: {
                "can_read": True,
                "can_create": True,
                "can_update": True, 
                "can_delete": False,
                "can_manage_permissions": False,
            },
            self.RoleChoices.COORDINATOR: {
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": False, 
                "can_manage_permissions": False,
            },
            self.RoleChoices.VIEWER: {
                "can_read": True,
                "can_create": False,
                "can_update": False,
                "can_delete": False,
                "can_manage_permissions": False,
            },
        }
        return role_perms.get(self.role, role_perms[self.RoleChoices.VIEWER])


class UserFieldPermission(CreatedAndUpdatedOnMixin, models.Model):
    """
    Permiso específico de campo para un usuario dentro de una regla de permisos.
    Permite control granular a nivel de campo individual.
    """
    
    class PermissionChoices(models.TextChoices):
        READ = "read", _("Read")
        WRITE = "write", _("Write") 
        HIDDEN = "hidden", _("Hidden")
    
    user_rule = models.ForeignKey(
        UserPermissionRule,
        on_delete=models.CASCADE,
        related_name="field_permissions",
        help_text=_("User permission rule this field permission belongs to")
    )
    field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name="user_permissions",
        help_text=_("Field to which this permission applies")
    )
    permission = models.CharField(
        max_length=10,
        choices=PermissionChoices.choices,
        default=PermissionChoices.READ,
        help_text=_("Permission level for this field")
    )
    
    class Meta:
        app_label = "user_permissions"
        db_table = "database_user_field_permission"
        unique_together = [["user_rule", "field"]]
        indexes = [
            models.Index(fields=["user_rule", "permission"]),
            models.Index(fields=["field", "permission"]),
        ]
        
    def __str__(self):
        return f"{self.field.name} - {self.permission} ({self.user_rule.user.email})"
        
    def clean(self):
        """Valida que el campo pertenezca a la misma tabla de la regla"""
        if self.field.table_id != self.user_rule.table_id:
            raise ValidationError(
                _("Field must belong to the same table as the user permission rule")
            )


class UserFilteredView(
    TrashableModelMixin,
    CreatedAndUpdatedOnMixin,
    models.Model
):
    """
    Vista personalizada para un usuario basada en sus permisos efectivos.
    Crea una vista dinámica que respeta las restricciones de permisos del usuario.
    """
    
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE, 
        related_name="user_filtered_views",
        help_text=_("Table for which this filtered view is created")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="filtered_views", 
        help_text=_("User for whom this filtered view is created")
    )
    name = models.CharField(
        max_length=255,
        help_text=_("Display name for this filtered view")
    )
    base_view = models.ForeignKey(
        View,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("Base view to inherit configuration from")
    )
    user_filters = models.JSONField(
        default=dict,
        blank=True,
        help_text=_(
            "Additional filters applied based on user permissions. "
            "These are merged with base_view filters and user permission row_filter"
        )
    )
    visible_fields = models.JSONField(
        default=list,
        blank=True,
        help_text=_("List of field IDs visible to this user")
    )
    is_default = models.BooleanField(
        default=False,
        help_text=_("Whether this is the default view for the user")
    )
    
    class Meta:
        app_label = "user_permissions"
        db_table = "database_user_filtered_view"
        unique_together = [["table", "user"]]
        indexes = [
            models.Index(fields=["table", "user"]),
            models.Index(fields=["user", "is_default"]),
        ]
        
    def __str__(self):
        return f"{self.name} - {self.user.email} ({self.table.name})"
        
    def clean(self):
        """Valida coherencia de la vista filtrada"""
        if self.base_view and self.base_view.table_id != self.table_id:
            raise ValidationError(
                _("Base view must belong to the same table")
            )
            
        # Validar que el usuario tenga permisos en la tabla
        if not UserPermissionRule.objects.filter(
            table=self.table, 
            user=self.user, 
            is_active=True
        ).exists():
            raise ValidationError(
                _("User must have active permissions on the table to create a filtered view")
            )


class UserPermissionAuditLog(CreatedAndUpdatedOnMixin, models.Model):
    """
    Log de auditoría para cambios en permisos de usuario.
    Mantiene trazabilidad de quién otorga/modifica/revoca permisos.
    """
    
    class ActionChoices(models.TextChoices):
        GRANTED = "granted", _("Granted")
        MODIFIED = "modified", _("Modified")
        REVOKED = "revoked", _("Revoked")
        FIELD_PERMISSION_SET = "field_permission_set", _("Field Permission Set")
        FIELD_PERMISSION_REMOVED = "field_permission_removed", _("Field Permission Removed")
    
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="permission_audit_logs"
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE, 
        related_name="permission_changes_received",
        help_text=_("User whose permissions were modified")
    )
    actor_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="permission_changes_made",
        help_text=_("User who made the permission change")
    )
    action = models.CharField(
        max_length=30,
        choices=ActionChoices.choices
    )
    details = models.JSONField(
        default=dict,
        help_text=_("Additional details about the permission change")
    )
    
    class Meta:
        app_label = "user_permissions"
        db_table = "database_user_permission_audit_log"
        indexes = [
            models.Index(fields=["table", "created_on"]),
            models.Index(fields=["target_user", "created_on"]),
            models.Index(fields=["actor_user", "created_on"]),
        ]
        
    def __str__(self):
        return f"{self.action} - {self.target_user.email} by {self.actor_user.email}"