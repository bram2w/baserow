"""
Patch para integrar permisos de usuario personalizados en FieldsView
Este archivo modifica el comportamiento del endpoint list_fields para filtrar campos según permisos de usuario
"""

from baserow.contrib.database.api.fields.views import FieldsView
from baserow.contrib.database.user_permissions.handler import UserPermissionHandler
from rest_framework.response import Response


# Guardar el método GET original
_original_get = FieldsView.get


def patched_get(self, request, table_id):
    """
    Versión parcheada del método GET que filtra campos según permisos de usuario
    """
    from baserow.contrib.database.table.handler import TableHandler
    from baserow.contrib.database.fields.handler import FieldHandler
    from baserow.contrib.database.api.fields.serializers import FieldSerializer
    from baserow.contrib.database.fields.registries import field_type_registry
    from baserow.contrib.database.fields.operations import ListFieldsOperationType
    from baserow.core.handler import CoreHandler
    from baserow.contrib.database.tokens.handler import TokenHandler
    from baserow.core.db import specific_iterator
    
    # Obtener la tabla
    table = TableHandler().get_table(table_id)
    
    # Verificar permisos base
    CoreHandler().check_permissions(
        request.user,
        ListFieldsOperationType.type,
        workspace=table.database.workspace,
        context=table,
    )
    
    TokenHandler().check_table_permissions(
        request, ["read", "create", "update"], table, False
    )
    
    # Obtener todos los campos
    base_field_queryset = FieldHandler().get_base_fields_queryset()
    fields = list(specific_iterator(
        base_field_queryset.filter(table=table),
        per_content_type_queryset_hook=(
            lambda field, queryset: field_type_registry.get_by_model(
                field
            ).enhance_field_queryset(queryset, field)
        ),
    ))
    
    # 🔐 APLICAR FILTRO DE PERMISOS DE USUARIO
    if request.user and request.user.is_authenticated:
        try:
            permission_handler = UserPermissionHandler()
            fields = permission_handler.filter_fields_by_user_permissions(
                fields=fields,
                user=request.user,
                table=table
            )
        except Exception as e:
            # Si hay error en el filtro, log pero continuar mostrando todos los campos
            print(f"⚠️  Error filtering fields by permissions: {e}")
    
    # Serializar y devolver
    data = [
        field_type_registry.get_serializer(field, FieldSerializer).data
        for field in fields
    ]
    return Response(data)


# Aplicar el patch
FieldsView.get = patched_get

print("✅ FieldsView patched successfully - User permissions will be applied to field listing")
