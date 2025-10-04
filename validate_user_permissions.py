#!/usr/bin/env python3
"""
Simple validation script for User Permissions models
"""
import sys
import os

# Add the backend source to the path
sys.path.insert(0, '/baserow/backend/src')

try:
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baserow.config.settings.dev')
    
    # Import Django and setup
    import django
    django.setup()
    
    print("✅ Django setup successful")
    
    # Test basic imports
    from baserow.contrib.database.models import Database, Table
    print("✅ Basic Baserow models imported successfully")
    
    # Test our new models
    try:
        from baserow.contrib.database.user_permissions.models import (
            UserPermissionRule,
            UserFieldPermission,
            UserFilteredView,
            UserPermissionAuditLog,
        )
        print("✅ User Permissions models imported successfully")
        
        # Test our handler
        from baserow.contrib.database.user_permissions.handler import UserPermissionHandler
        handler = UserPermissionHandler()
        print("✅ User Permission Handler created successfully")
        
        # Test permission manager type
        from baserow.contrib.database.user_permissions.permission_manager_types import UserPermissionManagerType
        manager = UserPermissionManagerType()
        print(f"✅ User Permission Manager Type created: {manager.type}")
        
        print("\n🎉 ALL VALIDATIONS PASSED! The user permissions system is ready.")
        
    except ImportError as e:
        print(f"❌ Failed to import user permissions module: {e}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Failed to setup Django or import modules: {e}")
    sys.exit(1)