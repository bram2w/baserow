import sys
sys.path.insert(0, '/baserow/backend/src')

try:
    from baserow.contrib.database.user_permissions.apps import UserPermissionsConfig
    print(f"✓ App importada correctamente: {UserPermissionsConfig.name}")
    
    # Verificar que está en INSTALLED_APPS
    from django.conf import settings
    if 'baserow.contrib.database.user_permissions' in settings.INSTALLED_APPS:
        print("✓ App está en INSTALLED_APPS")
    else:
        print("✗ App NO está en INSTALLED_APPS")
        print(f"INSTALLED_APPS contiene {len(settings.INSTALLED_APPS)} apps")
        
except Exception as e:
    print(f"✗ Error al importar: {e}")
    import traceback
    traceback.print_exc()
