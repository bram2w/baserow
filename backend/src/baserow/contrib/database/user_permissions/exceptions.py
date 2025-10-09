"""
User Permissions Exceptions - Excepciones específicas del sistema
Ubicación: backend/src/baserow/contrib/database/user_permissions/exceptions.py
"""

from rest_framework import status


ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST = (
    "ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST",
    status.HTTP_404_NOT_FOUND,
    "The user permission rule does not exist.",
)

ERROR_USER_PERMISSION_RULE_ALREADY_EXISTS = (
    "ERROR_USER_PERMISSION_RULE_ALREADY_EXISTS",
    status.HTTP_400_BAD_REQUEST,
    "A user permission rule already exists for this user and table.",
)

ERROR_INVALID_USER_CONTEXT_VARIABLE = (
    "ERROR_INVALID_USER_CONTEXT_VARIABLE",
    status.HTTP_400_BAD_REQUEST,
    "Invalid user context variable in row filter.",
)

ERROR_INVALID_ROW_FILTER = (
    "ERROR_INVALID_ROW_FILTER",
    status.HTTP_400_BAD_REQUEST,
    "Invalid row filter format or expression.",
)

ERROR_USER_FILTERED_VIEW_DOES_NOT_EXIST = (
    "ERROR_USER_FILTERED_VIEW_DOES_NOT_EXIST",
    status.HTTP_404_NOT_FOUND,
    "The user filtered view does not exist.",
)

ERROR_CANNOT_MANAGE_USER_PERMISSIONS = (
    "ERROR_CANNOT_MANAGE_USER_PERMISSIONS",
    status.HTTP_403_FORBIDDEN,
    "You do not have permission to manage user permissions for this table.",
)


# Exception Classes - Simple implementations
class UserPermissionRuleDoesNotExist(Exception):
    """Raised when a permission rule is not found"""
    pass


class UserPermissionRuleAlreadyExists(Exception):
    """Raised when trying to create a duplicate permission rule"""
    pass


class InvalidUserContextVariable(Exception):
    """Raised when row filter contains invalid context variables"""
    pass


class InvalidRowFilter(Exception):
    """Raised when row filter format is invalid"""
    pass


class UserFilteredViewDoesNotExist(Exception):
    """Raised when a filtered view is not found"""
    pass


class CannotManageUserPermissions(Exception):
    """Raised when user cannot manage permissions"""
    pass
