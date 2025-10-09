"""
User Permissions API Errors
Ubicación: backend/src/baserow/contrib/database/api/user_permissions/errors.py
"""

from rest_framework import status

# Import base error definitions from the main exceptions module
from baserow.contrib.database.user_permissions.exceptions import (
    ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST,
    ERROR_USER_PERMISSION_RULE_ALREADY_EXISTS,
    ERROR_INVALID_USER_CONTEXT_VARIABLE,
    ERROR_INVALID_ROW_FILTER,
    ERROR_USER_FILTERED_VIEW_DOES_NOT_EXIST,
    ERROR_CANNOT_MANAGE_USER_PERMISSIONS,
)

# Re-export for API use
__all__ = [
    "ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST",
    "ERROR_USER_PERMISSION_RULE_ALREADY_EXISTS",
    "ERROR_INVALID_USER_CONTEXT_VARIABLE",
    "ERROR_INVALID_ROW_FILTER",
    "ERROR_USER_FILTERED_VIEW_DOES_NOT_EXIST",
    "ERROR_CANNOT_MANAGE_USER_PERMISSIONS",
]