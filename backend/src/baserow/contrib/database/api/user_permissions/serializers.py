"""
User Permissions API Serializers
Ubicación: backend/src/baserow/contrib/database/api/user_permissions/serializers.py
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

from baserow.api.user.serializers import UserSerializer
from baserow.contrib.database.api.fields.serializers import FieldSerializer
from baserow.contrib.database.api.tables.serializers import TableSerializer
from baserow.contrib.database.user_permissions.models import (
    UserPermissionRule,
    UserFieldPermission,
    UserFilteredView,
    UserPermissionAuditLog,
)

User = get_user_model()


class UserPermissionRuleSerializer(serializers.ModelSerializer):
    """Serializer for UserPermissionRule model"""
    
    user = UserSerializer(read_only=True)
    table = TableSerializer(read_only=True)
    effective_permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPermissionRule
        fields = (
            "id",
            "user",
            "table", 
            "role",
            "row_filter",
            "is_active",
            "created_at",
            "updated_at",
            "effective_permissions",
        )
        read_only_fields = ("id", "user", "table", "created_at", "updated_at")
    
    def get_effective_permissions(self, obj):
        """Get calculated effective permissions for this rule"""
        return {
            "can_read": obj.role_permissions["can_read"],
            "can_create": obj.role_permissions["can_create"],
            "can_update": obj.role_permissions["can_update"],
            "can_delete": obj.role_permissions["can_delete"],
            "can_manage_permissions": obj.role_permissions["can_manage_permissions"],
        }

    def validate_row_filter(self, value):
        """Validate row filter contains only allowed user variables"""
        if not isinstance(value, dict):
            raise ValidationError("Row filter must be a valid JSON object")
            
        # Import here to avoid circular imports
        from baserow.contrib.database.user_permissions.handler import UserPermissionHandler
        
        handler = UserPermissionHandler()
        try:
            handler._validate_row_filter(value)
        except Exception as e:
            raise ValidationError(f"Invalid row filter: {str(e)}")
            
        return value


class CreateUserPermissionRuleSerializer(serializers.Serializer):
    """Serializer for creating new user permission rules"""
    
    user_id = serializers.IntegerField(
        min_value=1,
        help_text="ID of the user to grant permissions to"
    )
    role = serializers.ChoiceField(
        choices=UserPermissionRule.RoleChoices.choices,
        default=UserPermissionRule.RoleChoices.VIEWER,
        help_text="Role to assign to the user"
    )
    row_filter = serializers.JSONField(
        default=dict,
        required=False,
        help_text=(
            "JSON filter to limit visible rows using user context variables. "
            "Example: {\"assigned_to\": \"{user.id}\", \"department\": \"{user.department}\"}"
        )
    )
    field_permissions = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text=(
            "List of field-specific permissions. "
            "Each item should have 'field_id' and 'permission' keys"
        )
    )
    
    def validate_user_id(self, value):
        """Validate that user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise ValidationError("User does not exist")
        return value
    
    def validate_field_permissions(self, value):
        """Validate field permissions structure"""
        if not value:
            return value
            
        for item in value:
            if not isinstance(item, dict):
                raise ValidationError("Each field permission must be an object")
                
            if "field_id" not in item:
                raise ValidationError("field_id is required for each field permission")
                
            if "permission" not in item:
                raise ValidationError("permission is required for each field permission")
                
            try:
                field_id = int(item["field_id"])
                if field_id < 1:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValidationError("field_id must be a positive integer")
                
            if item["permission"] not in [
                UserFieldPermission.PermissionChoices.READ,
                UserFieldPermission.PermissionChoices.WRITE,
                UserFieldPermission.PermissionChoices.HIDDEN,
            ]:
                raise ValidationError(
                    f"Invalid permission: {item['permission']}. "
                    f"Must be one of: read, write, hidden"
                )
        
        return value
    
    def validate_row_filter(self, value):
        """Validate row filter format and variables"""
        if not isinstance(value, dict):
            raise ValidationError("Row filter must be a valid JSON object")
            
        # Import here to avoid circular imports
        from baserow.contrib.database.user_permissions.handler import UserPermissionHandler
        
        handler = UserPermissionHandler()
        try:
            handler._validate_row_filter(value)
        except Exception as e:
            raise ValidationError(f"Invalid row filter: {str(e)}")
            
        return value


class UpdateUserPermissionRuleSerializer(serializers.Serializer):
    """Serializer for updating existing user permission rules"""
    
    role = serializers.ChoiceField(
        choices=UserPermissionRule.RoleChoices.choices,
        required=False,
        help_text="New role to assign to the user"
    )
    row_filter = serializers.JSONField(
        required=False,
        help_text="New row filter configuration"
    )
    field_permissions = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text="Updated field permissions (replaces existing ones)"
    )
    
    def validate_field_permissions(self, value):
        """Validate field permissions structure"""
        if not value:
            return value
            
        serializer = CreateUserPermissionRuleSerializer()
        return serializer.validate_field_permissions(value)
    
    def validate_row_filter(self, value):
        """Validate row filter format and variables"""
        serializer = CreateUserPermissionRuleSerializer()
        return serializer.validate_row_filter(value)


class UserFieldPermissionSerializer(serializers.ModelSerializer):
    """Serializer for UserFieldPermission model"""
    
    field = FieldSerializer(read_only=True)
    
    class Meta:
        model = UserFieldPermission
        fields = (
            "id",
            "field",
            "permission",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "field", "created_at", "updated_at")


class UserFilteredViewSerializer(serializers.ModelSerializer):
    """Serializer for UserFilteredView model"""
    
    user = UserSerializer(read_only=True)
    table = TableSerializer(read_only=True)
    
    class Meta:
        model = UserFilteredView
        fields = (
            "id",
            "user",
            "table",
            "name", 
            "base_view_id",
            "user_filters",
            "visible_fields",
            "is_default",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user", 
            "table",
            "user_filters",
            "visible_fields",
            "created_at",
            "updated_at",
        )


class UserPermissionAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for UserPermissionAuditLog model"""
    
    target_user = UserSerializer(read_only=True)
    actor_user = UserSerializer(read_only=True)
    table = TableSerializer(read_only=True)
    
    class Meta:
        model = UserPermissionAuditLog
        fields = (
            "id",
            "table",
            "target_user",
            "actor_user", 
            "action",
            "details",
            "created_at",
        )
        read_only_fields = ("id", "table", "target_user", "actor_user", "action", "details", "created_at")


class UserPermissionsSummarySerializer(serializers.Serializer):
    """Serializer for user permissions summary response"""
    
    user = UserSerializer(read_only=True)
    table = TableSerializer(read_only=True)
    has_permissions = serializers.BooleanField(read_only=True)
    rule = UserPermissionRuleSerializer(read_only=True, allow_null=True)
    field_permissions = UserFieldPermissionSerializer(many=True, read_only=True)
    filtered_view = UserFilteredViewSerializer(read_only=True, allow_null=True)
    effective_permissions = serializers.DictField(read_only=True)
    
    class Meta:
        fields = (
            "user",
            "table", 
            "has_permissions",
            "rule",
            "field_permissions",
            "filtered_view",
            "effective_permissions",
        )