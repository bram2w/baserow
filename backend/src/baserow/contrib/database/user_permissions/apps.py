"""
User Permissions App Configuration
"""

from django.apps import AppConfig


class UserPermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'baserow.contrib.database.user_permissions'
    
    def ready(self):
        """Import signals when app is ready"""
        # Import signals to activate receivers
        from . import signals  # noqa: F401
        
        # Apply field permissions patch to FieldsView
        from . import field_permissions_patch  # noqa: F401
        
        # Row filter patch NO LONGER NEEDED - using direct source code modification in views.py
        # from . import row_filter_patch  # noqa: F401
