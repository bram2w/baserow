"""
User Permissions API Views
Ubicación: backend/src/baserow/contrib/database/api/user_permissions/views.py
"""

from django.contrib.auth import get_user_model
from django.db import transaction

from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.contrib.database.api.tables.errors import ERROR_TABLE_DOES_NOT_EXIST
from baserow.contrib.database.api.tokens.authentications import TokenAuthentication
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.user_permissions.handler import UserPermissionHandler
from baserow.contrib.database.user_permissions.exceptions import (
    UserPermissionRuleDoesNotExist,
    UserPermissionRuleAlreadyExists,
    InvalidUserContextVariable,
    CannotManageUserPermissions,
)
from baserow.core.exceptions import UserNotInWorkspace
from baserow.core.handler import CoreHandler

from .errors import (
    ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST,
    ERROR_USER_PERMISSION_RULE_ALREADY_EXISTS,
    ERROR_INVALID_USER_CONTEXT_VARIABLE,
    ERROR_CANNOT_MANAGE_USER_PERMISSIONS,
)
from .serializers import (
    CreateUserPermissionRuleSerializer,
    UpdateUserPermissionRuleSerializer,
    UserPermissionRuleSerializer,
    UserFieldPermissionSerializer,
    UserFilteredViewSerializer,
    UserPermissionAuditLogSerializer,
    UserPermissionsSummarySerializer,
)

User = get_user_model()


class UserPermissionRulesView(APIView):
    """
    API view for managing user permission rules for a specific table.
    
    Supports:
    - GET: List all user permission rules for a table
    - POST: Create new user permission rule
    """
    
    authentication_classes = APIView.authentication_classes + [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the user permission rules for the table related to the provided value.",
            )
        ],
        tags=["Database table user permissions"],
        operation_id="list_table_user_permission_rules",
        description=(
            "Lists all user permission rules for the specified table. "
            "Only users with admin permissions on the table can access this endpoint."
        ),
        responses={
            200: UserPermissionRuleSerializer(many=True),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, table_id):
        """List all user permission rules for a table"""
        table = TableHandler().get_table(table_id)
        
        # Check if user has permission to manage permissions
        handler = UserPermissionHandler()
        handler._check_can_manage_permissions(request.user, table)
        
        # Get all active permission rules for the table
        rules = table.user_permission_rules.filter(is_active=True).select_related(
            "user", "table"
        ).prefetch_related("field_permissions__field")
        
        serializer = UserPermissionRuleSerializer(rules, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates a user permission rule for the table related to the provided value.",
            )
        ],
        tags=["Database table user permissions"],
        operation_id="create_table_user_permission_rule",
        description=(
            "Creates a new user permission rule for the specified table. "
            "Allows granting specific permissions to a user with optional row-level "
            "filtering and field-level permissions."
        ),
        request=CreateUserPermissionRuleSerializer,
        responses={
            201: UserPermissionRuleSerializer,
            400: get_error_schema([
                "ERROR_USER_NOT_IN_GROUP",
                "ERROR_USER_PERMISSION_RULE_ALREADY_EXISTS",
                "ERROR_INVALID_USER_CONTEXT_VARIABLE",
            ]),
            403: get_error_schema(["ERROR_CANNOT_MANAGE_USER_PERMISSIONS"]),
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body(CreateUserPermissionRuleSerializer)
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserPermissionRuleAlreadyExists: ERROR_USER_PERMISSION_RULE_ALREADY_EXISTS,
            InvalidUserContextVariable: ERROR_INVALID_USER_CONTEXT_VARIABLE,
            CannotManageUserPermissions: ERROR_CANNOT_MANAGE_USER_PERMISSIONS,
        }
    )
    def post(self, request, table_id, data):
        """Create a new user permission rule"""
        table = TableHandler().get_table(table_id)
        target_user = User.objects.get(id=data["user_id"])
        
        # Create the permission rule
        handler = UserPermissionHandler()
        rule = handler.grant_user_permission(
            actor=request.user,
            table=table,
            user=target_user,
            role=data["role"],
            row_filter=data.get("row_filter", {}),
            field_permissions=data.get("field_permissions", []),
        )
        
        serializer = UserPermissionRuleSerializer(rule)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserPermissionRuleView(APIView):
    """
    API view for managing individual user permission rules.
    
    Supports:
    - GET: Get details of a specific user permission rule
    - PATCH: Update an existing user permission rule  
    - DELETE: Revoke user permissions (soft delete)
    """
    
    authentication_classes = APIView.authentication_classes + [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the user permission rule for the table related to the provided value.",
            ),
            OpenApiParameter(
                name="user_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the user permission rule for the user related to the provided value.",
            ),
        ],
        tags=["Database table user permissions"],
        operation_id="get_table_user_permission_rule",
        description="Returns details of a specific user permission rule.",
        responses={
            200: UserPermissionRuleSerializer,
            404: get_error_schema([
                "ERROR_TABLE_DOES_NOT_EXIST",
                "ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST",
            ]),
        },
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserPermissionRuleDoesNotExist: ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST,
        }
    )
    def get(self, request, table_id, user_id):
        """Get details of a user permission rule"""
        table = TableHandler().get_table(table_id)
        target_user = User.objects.get(id=user_id)
        
        handler = UserPermissionHandler()
        rule = handler.get_user_permission_rule(table, target_user)
        
        if rule is None:
            raise UserPermissionRuleDoesNotExist()
            
        serializer = UserPermissionRuleSerializer(rule)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the user permission rule for the table related to the provided value.",
            ),
            OpenApiParameter(
                name="user_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the user permission rule for the user related to the provided value.",
            ),
        ],
        tags=["Database table user permissions"],
        operation_id="update_table_user_permission_rule",
        description=(
            "Updates an existing user permission rule. "
            "Allows changing role, row filters, and field permissions."
        ),
        request=UpdateUserPermissionRuleSerializer,
        responses={
            200: UserPermissionRuleSerializer,
            400: get_error_schema([
                "ERROR_USER_NOT_IN_GROUP",
                "ERROR_INVALID_USER_CONTEXT_VARIABLE",
            ]),
            403: get_error_schema(["ERROR_CANNOT_MANAGE_USER_PERMISSIONS"]),
            404: get_error_schema([
                "ERROR_TABLE_DOES_NOT_EXIST",
                "ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST",
            ]),
        },
    )
    @transaction.atomic
    @validate_body(UpdateUserPermissionRuleSerializer)
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            UserPermissionRuleDoesNotExist: ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST,
            InvalidUserContextVariable: ERROR_INVALID_USER_CONTEXT_VARIABLE,
            CannotManageUserPermissions: ERROR_CANNOT_MANAGE_USER_PERMISSIONS,
        }
    )
    def patch(self, request, table_id, user_id, data):
        """Update an existing user permission rule"""
        table = TableHandler().get_table(table_id)
        target_user = User.objects.get(id=user_id)
        
        handler = UserPermissionHandler()
        rule = handler.update_user_permission(
            actor=request.user,
            table=table,
            user=target_user,
            role=data.get("role"),
            row_filter=data.get("row_filter"),
            field_permissions=data.get("field_permissions"),
        )
        
        serializer = UserPermissionRuleSerializer(rule)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Revokes user permissions for the table related to the provided value.",
            ),
            OpenApiParameter(
                name="user_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Revokes user permissions for the user related to the provided value.",
            ),
        ],
        tags=["Database table user permissions"],
        operation_id="revoke_table_user_permission_rule",
        description=(
            "Revokes all permissions for a user on the specified table. "
            "This performs a soft delete - the rule is marked inactive but preserved for audit."
        ),
        responses={
            204: None,
            403: get_error_schema(["ERROR_CANNOT_MANAGE_USER_PERMISSIONS"]),
            404: get_error_schema([
                "ERROR_TABLE_DOES_NOT_EXIST",
                "ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST",
            ]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            CannotManageUserPermissions: ERROR_CANNOT_MANAGE_USER_PERMISSIONS,
        }
    )
    def delete(self, request, table_id, user_id):
        """Revoke user permissions"""
        table = TableHandler().get_table(table_id)
        target_user = User.objects.get(id=user_id)
        
        handler = UserPermissionHandler()
        revoked = handler.revoke_user_permission(
            actor=request.user,
            table=table,
            user=target_user,
        )
        
        if not revoked:
            raise UserPermissionRuleDoesNotExist()
            
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserPermissionsSummaryView(APIView):
    """
    API view for getting comprehensive user permissions summary.
    
    Returns effective permissions, field permissions, and filtered views for a user.
    """
    
    authentication_classes = APIView.authentication_classes + [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the user permissions summary for the table related to the provided value.",
            ),
            OpenApiParameter(
                name="user_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the user permissions summary for the user related to the provided value.",
            ),
        ],
        tags=["Database table user permissions"],
        operation_id="get_user_permissions_summary",
        description=(
            "Returns a comprehensive summary of user permissions including "
            "effective permissions, field-level permissions, and filtered views."
        ),
        responses={
            200: UserPermissionsSummarySerializer,
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, table_id, user_id):
        """Get comprehensive user permissions summary"""
        table = TableHandler().get_table(table_id)
        target_user = User.objects.get(id=user_id)
        
        handler = UserPermissionHandler()
        
        # Get user permission rule
        rule = handler.get_user_permission_rule(table, target_user)
        
        # Get effective permissions
        effective_permissions = handler.get_effective_permissions(target_user, table)
        
        # Get field permissions
        field_permissions = []
        if rule:
            field_permissions = rule.field_permissions.select_related("field").all()
            
        # Get filtered view
        filtered_view = handler.get_user_filtered_view(target_user, table)
        
        response_data = {
            "user": target_user,
            "table": table,
            "has_permissions": rule is not None,
            "rule": rule,
            "field_permissions": field_permissions,
            "filtered_view": filtered_view,
            "effective_permissions": effective_permissions,
        }
        
        serializer = UserPermissionsSummarySerializer(response_data)
        return Response(serializer.data)


class UserFilteredViewView(APIView):
    """
    API view for managing user filtered views.
    
    Supports:
    - GET: Get user's filtered view for a table
    - POST: Create or refresh user's filtered view
    """
    
    authentication_classes = APIView.authentication_classes + [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the filtered view for the table related to the provided value.",
            ),
        ],
        tags=["Database table user permissions"],
        operation_id="get_user_filtered_view",
        description=(
            "Returns the current user's filtered view for the specified table. "
            "The view reflects the user's permission-based field visibility and row filters."
        ),
        responses={
            200: UserFilteredViewSerializer,
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, table_id):
        """Get user's filtered view for a table"""
        table = TableHandler().get_table(table_id)
        
        handler = UserPermissionHandler()
        filtered_view = handler.get_user_filtered_view(request.user, table)
        
        if filtered_view is None:
            return Response({"detail": "No filtered view available for this user"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserFilteredViewSerializer(filtered_view)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates or refreshes filtered view for the table related to the provided value.",
            ),
        ],
        tags=["Database table user permissions"],
        operation_id="refresh_user_filtered_view",
        description=(
            "Creates or refreshes the current user's filtered view for the specified table. "
            "This updates the view to reflect any recent changes in user permissions."
        ),
        responses={
            200: UserFilteredViewSerializer,
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def post(self, request, table_id):
        """Create or refresh user's filtered view"""
        table = TableHandler().get_table(table_id)
        
        # Delete existing view to force refresh
        from baserow.contrib.database.user_permissions.models import UserFilteredView
        UserFilteredView.objects.filter(table=table, user=request.user).delete()
        
        handler = UserPermissionHandler()
        filtered_view = handler.get_user_filtered_view(request.user, table)
        
        if filtered_view is None:
            return Response({"detail": "No permissions available for this user"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserFilteredViewSerializer(filtered_view)
        return Response(serializer.data)


class UserPermissionAuditLogView(APIView):
    """
    API view for accessing user permission audit logs.
    """
    
    authentication_classes = APIView.authentication_classes + [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns audit logs for the table related to the provided value.",
            ),
        ],
        tags=["Database table user permissions"],
        operation_id="list_user_permission_audit_logs",
        description=(
            "Lists audit log entries for user permission changes on the specified table. "
            "Only users with admin permissions can access audit logs."
        ),
        responses={
            200: UserPermissionAuditLogSerializer(many=True),
            403: get_error_schema(["ERROR_CANNOT_MANAGE_USER_PERMISSIONS"]),
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            CannotManageUserPermissions: ERROR_CANNOT_MANAGE_USER_PERMISSIONS,
        }
    )
    def get(self, request, table_id):
        """List audit logs for user permission changes"""
        table = TableHandler().get_table(table_id)
        
        # Check if user has permission to view audit logs
        handler = UserPermissionHandler()
        handler._check_can_manage_permissions(request.user, table)
        
        # Get audit logs for the table
        audit_logs = table.permission_audit_logs.select_related(
            "target_user", "actor_user", "table"
        ).order_by("-created_at")[:100]  # Limit to last 100 entries
        
        serializer = UserPermissionAuditLogSerializer(audit_logs, many=True)
        return Response(serializer.data)