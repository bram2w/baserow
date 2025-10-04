"""
User Permission Manager Type - Integración con sistema de permisos de Baserow
Ubicación: backend/src/baserow/contrib/database/user_permissions/permission_manager_types.py
"""

from typing import Any, Dict, Optional, Union
from django.contrib.auth.models import AbstractUser, AnonymousUser

from baserow.contrib.database.table.models import Table
from baserow.contrib.database.fields.models import Field  
from baserow.core.registries import PermissionManagerType
from baserow.core.exceptions import PermissionDenied

from .handler import UserPermissionHandler
from .models import UserPermissionRule


class UserPermissionManagerType(PermissionManagerType):
    """
    Permission Manager que maneja permisos granulares por usuario.
    Se integra con el sistema de registros existente de Baserow.
    """
    
    type = "user_permissions"
    
    def __init__(self):
        self.handler = UserPermissionHandler()
    
    def get_permissions_object(
        self,
        actor: Union[AbstractUser, AnonymousUser], 
        workspace=None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retorna objeto de permisos efectivos para el actor en el contexto dado.
        
        :param actor: Usuario o usuario anónimo
        :param workspace: Workspace opcional
        :param context: Contexto adicional que puede incluir table, field, row
        :return: Diccionario con permisos efectivos
        """
        if isinstance(actor, AnonymousUser):
            return self._get_anonymous_permissions()
            
        # Si no hay contexto específico, retornar permisos base
        if not context:
            return self._get_base_permissions()
            
        # Obtener tabla del contexto
        table = self._extract_table_from_context(context)
        if not table:
            return self._get_base_permissions()
            
        # Calcular permisos efectivos para la tabla
        return self.handler.get_effective_permissions(actor, table)
    
    def check_permissions(
        self,
        actor: Union[AbstractUser, AnonymousUser],
        operation: str,
        workspace=None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Verifica si el actor tiene permisos para realizar una operación específica.
        
        :param actor: Usuario que intenta realizar la operación
        :param operation: Operación a verificar (ej: 'database.table.read')
        :param workspace: Workspace en el cual verificar permisos
        :param context: Contexto adicional con objetos específicos
        :return: True si tiene permisos, False si no
        """
        if isinstance(actor, AnonymousUser):
            return False
            
        # Si no hay contexto específico, delegar al sistema base
        if not context:
            return True  # Delegar a otros permission managers
            
        table = self._extract_table_from_context(context)
        if not table:
            return True  # No es una operación relacionada con tablas
            
        # Verificar si el usuario tiene reglas específicas para esta tabla
        user_rule = self.handler.get_user_permission_rule(table, actor)
        if user_rule is None:
            return True  # No hay reglas específicas, delegar al sistema base
            
        # Verificar permisos según la operación solicitada
        permissions = self.handler.get_effective_permissions(actor, table)
        
        return self._check_operation_permission(operation, permissions, context)
    
    def filter_queryset(
        self,
        actor: Union[AbstractUser, AnonymousUser],
        operation: str,
        queryset,
        workspace=None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Filtra un queryset según los permisos del usuario.
        
        :param actor: Usuario para el cual filtrar
        :param operation: Operación que se está realizando
        :param queryset: QuerySet a filtrar
        :param workspace: Workspace actual
        :param context: Contexto adicional
        :return: QuerySet filtrado
        """
        if isinstance(actor, AnonymousUser):
            return queryset.none()
            
        # Detectar si es un queryset de filas (rows)
        if hasattr(queryset.model, 'table'):
            table = self._get_table_from_row_queryset(queryset)
            if table:
                return self.handler.apply_row_filters(actor, table, queryset)
                
        return queryset
    
    def get_role_assignments(
        self,
        workspace=None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retorna asignaciones de roles para el contexto dado.
        
        :param workspace: Workspace para el cual obtener roles
        :param context: Contexto específico
        :return: Diccionario con asignaciones de roles
        """
        if not context or 'table' not in context:
            return {}
            
        table = context['table']
        
        # Obtener todas las reglas de permisos para la tabla
        user_rules = UserPermissionRule.objects.filter(
            table=table,
            is_active=True
        ).select_related('user')
        
        assignments = {}
        for rule in user_rules:
            assignments[rule.user.email] = {
                'role': rule.role,
                'permissions': rule.role_permissions,
                'has_row_filter': bool(rule.row_filter),
                'field_permissions_count': rule.field_permissions.count(),
            }
            
        return assignments
    
    # Métodos privados de ayuda
    
    def _extract_table_from_context(self, context: Dict[str, Any]) -> Optional[Table]:
        """Extrae tabla del contexto si está disponible"""
        # Buscar tabla directamente
        if 'table' in context and isinstance(context['table'], Table):
            return context['table']
            
        # Buscar tabla a través de campo
        if 'field' in context and isinstance(context['field'], Field):
            return context['field'].table
            
        # Buscar tabla a través de fila
        if 'row' in context:
            row = context['row']
            if hasattr(row, 'table'):
                return row.table
                
        return None
    
    def _get_table_from_row_queryset(self, queryset) -> Optional[Table]:
        """Obtiene tabla de un queryset de filas"""
        try:
            # Intentar obtener tabla del modelo de fila
            if hasattr(queryset.model, 'table'):
                # Para RowForTable models dinámicos
                return queryset.model.table
        except:
            pass
            
        return None
    
    def _check_operation_permission(
        self, 
        operation: str, 
        permissions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Verifica permisos específicos según la operación"""
        operation_map = {
            'database.table.read': 'can_read',
            'database.table.create': 'can_create', 
            'database.table.update': 'can_update',
            'database.table.delete': 'can_delete',
            'database.rows.read': 'can_read',
            'database.rows.create': 'can_create',
            'database.rows.update': 'can_update',
            'database.rows.delete': 'can_delete',
        }
        
        permission_key = operation_map.get(operation)
        if not permission_key:
            return True  # Operación no manejada por este manager
            
        base_permission = permissions.get(permission_key, False)
        if not base_permission:
            return False
            
        # Verificar permisos a nivel de campo si es necesario
        if 'field' in context:
            return self._check_field_permission(context['field'], permissions, operation)
            
        return True
    
    def _check_field_permission(
        self, 
        field: Field, 
        permissions: Dict[str, Any], 
        operation: str
    ) -> bool:
        """Verifica permisos específicos de campo"""
        visible_fields = permissions.get('visible_fields', [])
        
        # Si el campo no está en la lista de visibles, está oculto
        if field.id not in visible_fields:
            return False
            
        # Para operaciones de escritura, verificar permisos específicos
        if 'update' in operation or 'create' in operation:
            # Aquí se podría implementar lógica más granular
            # por ahora, si es visible y tiene permisos base, permitir
            return True
            
        return True
    
    def _get_anonymous_permissions(self) -> Dict[str, Any]:
        """Permisos para usuarios anónimos"""
        return {
            'can_read': False,
            'can_create': False,
            'can_update': False, 
            'can_delete': False,
            'can_manage_permissions': False,
            'visible_fields': [],
            'has_row_filter': False,
            'row_filter': {},
        }
    
    def _get_base_permissions(self) -> Dict[str, Any]:
        """Permisos base cuando no hay contexto específico"""
        return {
            'can_read': True,
            'can_create': True,
            'can_update': True,
            'can_delete': True, 
            'can_manage_permissions': True,
            'visible_fields': [],
            'has_row_filter': False,
            'row_filter': {},
        }