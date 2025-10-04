"""
User Permissions Handler - Contratos de Servicios
Ubicación: backend/src/baserow/contrib/database/user_permissions/handler.py
"""

from typing import Dict, List, Optional, Union
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, QuerySet

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.models import Table  
from baserow.contrib.database.views.models import View
from baserow.core.exceptions import UserNotInWorkspace
from baserow.core.handler import CoreHandler

from .exceptions import (
    UserPermissionRuleDoesNotExist,
    UserPermissionRuleAlreadyExists,
    InvalidUserContextVariable,
    InvalidRowFilter,
)
from .models import (
    UserPermissionRule,
    UserFieldPermission, 
    UserFilteredView,
    UserPermissionAuditLog,
)

User = get_user_model()


class UserPermissionHandler:
    """
    Handler principal para gestionar permisos por usuario.
    Sigue el patrón Handler de Baserow para operaciones de negocio.
    """
    
    # Variables de contexto permitidas para filtros de fila
    ALLOWED_USER_VARIABLES = {
        'user.id': lambda user: user.id,
        'user.email': lambda user: user.email,
        'user.first_name': lambda user: user.first_name,
        'user.last_name': lambda user: user.last_name, 
        'user.username': lambda user: getattr(user, 'username', user.email),
        'user.is_staff': lambda user: user.is_staff,
        'user.date_joined': lambda user: user.date_joined.isoformat(),
        'user.groups': lambda user: list(user.groups.values_list('name', flat=True)),
        'user.profile.department': lambda user: getattr(user.profile, 'department', None),
    }
    
    def get_user_permission_rule(
        self, 
        table: Table, 
        user
    ) -> Optional[UserPermissionRule]:
        """
        Obtiene la regla de permisos activa para un usuario en una tabla.
        
        :param table: Tabla para la cual obtener permisos
        :param user: Usuario para el cual obtener permisos
        :return: Regla de permisos o None si no existe
        :raises UserNotInWorkspace: Si el usuario no pertenece al workspace
        """
        # TODO: Agregar verificación de permisos de workspace cuando esté disponible
        # CoreHandler().check_user_workspace_permissions(
        #     user, table.database.workspace, raise_error=True
        # )
        
        try:
            return UserPermissionRule.objects.select_related('table', 'user').get(
                table=table,
                user=user, 
                is_active=True
            )
        except UserPermissionRule.DoesNotExist:
            return None
            return None
    
    @transaction.atomic
    def grant_user_permission(
        self,
        actor,
        table: Table,
        user, 
        role: str,
        row_filter: Optional[Dict] = None,
        field_permissions: Optional[List[Dict]] = None,
    ) -> UserPermissionRule:
        """
        Otorga permisos a un usuario para una tabla específica.
        
        :param actor: Usuario que otorga los permisos (debe tener permisos de admin)
        :param table: Tabla para la cual otorgar permisos
        :param user: Usuario al cual otorgar permisos
        :param role: Rol base a asignar ('admin', 'manager', 'coordinator', 'viewer')
        :param row_filter: Filtro opcional de filas usando variables de usuario
        :param field_permissions: Lista de permisos específicos por campo
        :return: Regla de permisos creada
        :raises UserPermissionRuleAlreadyExists: Si ya existe una regla para este usuario
        :raises InvalidRowFilter: Si el filtro de filas contiene variables inválidas
        """
        # Validar que el actor tenga permisos para otorgar permisos
        self._check_can_manage_permissions(actor, table)
        
        # Validar que el usuario objetivo esté en el workspace
        CoreHandler().check_user_workspace_permissions(
            user, table.database.workspace, raise_error=True
        )
        
        # Validar que no exista ya una regla activa
        if self.get_user_permission_rule(table, user) is not None:
            raise UserPermissionRuleAlreadyExists(
                f"User {user.email} already has permissions for table {table.name}"
            )
            
        # Validar filtro de filas si se proporciona
        if row_filter:
            self._validate_row_filter(row_filter)
        
        # Crear regla de permisos principal
        user_rule = UserPermissionRule.objects.create(
            table=table,
            user=user,
            role=role,
            row_filter=row_filter or {},
        )
        
        # Crear permisos específicos de campo si se proporcionan
        if field_permissions:
            self._create_field_permissions(user_rule, field_permissions)
            
        # Registrar en audit log
        UserPermissionAuditLog.objects.create(
            table=table,
            target_user=user,
            actor_user=actor,
            action=UserPermissionAuditLog.ActionChoices.GRANTED,
            details={
                'role': role,
                'row_filter': row_filter,
                'field_permissions_count': len(field_permissions) if field_permissions else 0,
            }
        )
        
        return user_rule
    
    @transaction.atomic 
    def update_user_permission(
        self,
        actor,
        table: Table,
        user,
        role: Optional[str] = None,
        row_filter: Optional[Dict] = None,
        field_permissions: Optional[List[Dict]] = None,
    ) -> UserPermissionRule:
        """
        Actualiza los permisos existentes de un usuario.
        
        :param actor: Usuario que modifica los permisos
        :param table: Tabla para la cual modificar permisos
        :param user: Usuario cuyos permisos se modifican
        :param role: Nuevo rol base (opcional)
        :param row_filter: Nuevo filtro de filas (opcional)
        :param field_permissions: Nuevos permisos de campo (opcional)
        :return: Regla de permisos actualizada
        :raises UserPermissionRuleDoesNotExist: Si no existe regla para este usuario
        """
        self._check_can_manage_permissions(actor, table)
        
        user_rule = self.get_user_permission_rule(table, user)
        if user_rule is None:
            raise UserPermissionRuleDoesNotExist(
                f"No permission rule exists for user {user.email} on table {table.name}"
            )
            
        # Actualizar campos si se proporcionan
        updated_fields = {}
        if role is not None:
            user_rule.role = role
            updated_fields['role'] = role
            
        if row_filter is not None:
            self._validate_row_filter(row_filter)
            user_rule.row_filter = row_filter
            updated_fields['row_filter'] = row_filter
            
        user_rule.save()
        
        # Actualizar permisos de campo si se proporcionan
        if field_permissions is not None:
            # Eliminar permisos existentes y crear nuevos
            user_rule.field_permissions.all().delete()
            self._create_field_permissions(user_rule, field_permissions)
            updated_fields['field_permissions_count'] = len(field_permissions)
            
        # Registrar en audit log
        UserPermissionAuditLog.objects.create(
            table=table,
            target_user=user,
            actor_user=actor, 
            action=UserPermissionAuditLog.ActionChoices.MODIFIED,
            details=updated_fields
        )
        
        return user_rule
    
    @transaction.atomic
    def revoke_user_permission(
        self,
        actor,
        table: Table, 
        user,
    ) -> bool:
        """
        Revoca todos los permisos de un usuario para una tabla.
        
        :param actor: Usuario que revoca los permisos
        :param table: Tabla de la cual revocar permisos
        :param user: Usuario al cual revocar permisos
        :return: True si se revocaron permisos, False si no existían
        :raises PermissionDenied: Si el actor no tiene permisos para revocar
        """
        self._check_can_manage_permissions(actor, table)
        
        user_rule = self.get_user_permission_rule(table, user)
        if user_rule is None:
            return False
            
        # Marcar como inactiva en lugar de eliminar (soft delete)
        user_rule.is_active = False
        user_rule.save()
        
        # Eliminar vista filtrada asociada si existe
        UserFilteredView.objects.filter(table=table, user=user).delete()
        
        # Registrar en audit log
        UserPermissionAuditLog.objects.create(
            table=table,
            target_user=user,
            actor_user=actor,
            action=UserPermissionAuditLog.ActionChoices.REVOKED,
            details={'previous_role': user_rule.role}
        )
        
        return True
    
    def get_effective_permissions(
        self, 
        user, 
        table: Table
    ) -> Dict:
        """
        Calcula los permisos efectivos de un usuario para una tabla.
        Combina permisos de workspace, rol enterprise y permisos de usuario.
        
        :param user: Usuario para el cual calcular permisos
        :param table: Tabla para la cual calcular permisos  
        :return: Diccionario con permisos efectivos
        """
        # Obtener permisos base del workspace/tabla
        base_permissions = CoreHandler().check_permissions(
            user, 'database.table.read', table=table, raise_error=False
        )
        
        if not base_permissions:
            # Si no tiene permisos base, denegar todo
            return self._get_empty_permissions()
            
        # Obtener regla de permisos de usuario específica
        user_rule = self.get_user_permission_rule(table, user)
        if user_rule is None:
            # Sin permisos específicos, usar permisos base del workspace
            return self._get_base_table_permissions(user, table)
            
        # Combinar permisos de rol con permisos base
        role_permissions = user_rule.role_permissions
        
        # Obtener campos visibles según permisos específicos
        visible_fields = self._get_visible_fields_for_user(user_rule)
        
        return {
            'can_read': role_permissions['can_read'],
            'can_create': role_permissions['can_create'],
            'can_update': role_permissions['can_update'], 
            'can_delete': role_permissions['can_delete'],
            'can_manage_permissions': role_permissions['can_manage_permissions'],
            'visible_fields': visible_fields,
            'has_row_filter': bool(user_rule.row_filter),
            'row_filter': user_rule.row_filter,
        }
    
    def apply_row_filters(
        self,
        user,
        table: Table, 
        queryset: QuerySet
    ) -> QuerySet:
        """
        Aplica filtros de fila basados en permisos del usuario.
        
        :param user: Usuario para el cual aplicar filtros
        :param table: Tabla sobre la cual filtrar
        :param queryset: QuerySet base a filtrar
        :return: QuerySet filtrado según permisos del usuario
        """
        user_rule = self.get_user_permission_rule(table, user)
        if user_rule is None or not user_rule.row_filter:
            return queryset
            
        # Resolver variables de usuario en el filtro
        resolved_filter = self._resolve_user_variables(user_rule.row_filter, user)
        
        # Aplicar filtro al queryset
        if resolved_filter:
            return queryset.filter(**resolved_filter)
            
        return queryset
    
    def get_user_filtered_view(
        self,
        user,
        table: Table,
        base_view: Optional[View] = None
    ) -> Optional[UserFilteredView]:
        """
        Obtiene o crea una vista filtrada para un usuario basada en sus permisos.
        
        :param user: Usuario para el cual obtener la vista
        :param table: Tabla para la cual crear la vista
        :param base_view: Vista base opcional para heredar configuración
        :return: Vista filtrada del usuario o None si no tiene permisos
        """
        user_rule = self.get_user_permission_rule(table, user)
        if user_rule is None:
            return None
            
        try:
            user_view = UserFilteredView.objects.get(table=table, user=user)
        except UserFilteredView.DoesNotExist:
            # Crear vista filtrada automáticamente
            user_view = self._create_user_filtered_view(user_rule, base_view)
            
        return user_view
    
    # Métodos privados de ayuda
    
    def _check_can_manage_permissions(self, actor, table: Table) -> None:
        """Verifica que el actor tenga permisos para gestionar permisos de otros"""
        # TODO: Implementar verificación de permisos completa
        # Por ahora permitimos la operación
        pass
    
    def _validate_row_filter(self, row_filter: Dict) -> None:
        """Valida que el filtro de filas use solo variables permitidas"""
        filter_str = str(row_filter)
        
        # Buscar patrones {user.variable} en el filtro
        import re
        variables = re.findall(r'\{([^}]+)\}', filter_str)
        
        for var in variables:
            if var not in self.ALLOWED_USER_VARIABLES:
                raise InvalidUserContextVariable(
                    f"Variable '{var}' is not allowed in row filters. "
                    f"Allowed variables: {', '.join(self.ALLOWED_USER_VARIABLES.keys())}"
                )
    
    def _resolve_user_variables(self, row_filter: Dict, user) -> Dict:
        """Resuelve variables de usuario en un filtro de filas"""
        import json
        
        # Convertir a string para reemplazar variables
        filter_str = json.dumps(row_filter)
        
        # Reemplazar cada variable con su valor real
        for var_name, resolver in self.ALLOWED_USER_VARIABLES.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in filter_str:
                try:
                    value = resolver(user)
                    # Manejar diferentes tipos de datos
                    if isinstance(value, str):
                        replacement = f'"{value}"'
                    else:
                        replacement = json.dumps(value)
                    filter_str = filter_str.replace(f'"{placeholder}"', replacement)
                except Exception as e:
                    # Si no se puede resolver, mantener el filtro original
                    continue
        
        try:
            return json.loads(filter_str)
        except json.JSONDecodeError:
            return {}
    
    def _create_field_permissions(
        self, 
        user_rule: UserPermissionRule, 
        field_permissions: List[Dict]
    ) -> None:
        """Crea permisos específicos de campo para una regla de usuario"""
        field_permission_objects = []
        
        for field_perm in field_permissions:
            field_id = field_perm.get('field_id')
            permission = field_perm.get('permission', 'read')
            
            try:
                field = Field.objects.get(id=field_id, table=user_rule.table)
                field_permission_objects.append(
                    UserFieldPermission(
                        user_rule=user_rule,
                        field=field,
                        permission=permission
                    )
                )
            except Field.DoesNotExist:
                continue
                
        if field_permission_objects:
            UserFieldPermission.objects.bulk_create(field_permission_objects)
    
    def _get_visible_fields_for_user(self, user_rule: UserPermissionRule) -> List[int]:
        """Obtiene lista de IDs de campos visibles para un usuario"""
        # Obtener todos los campos de la tabla
        all_fields = user_rule.table.field_set.filter(trashed=False)
        
        # Obtener permisos específicos de campo
        field_permissions = {
            fp.field_id: fp.permission 
            for fp in user_rule.field_permissions.all()
        }
        
        visible_field_ids = []
        for field in all_fields:
            permission = field_permissions.get(field.id, 'read')  # Default: read
            if permission != 'hidden':
                visible_field_ids.append(field.id)
                
        return visible_field_ids
    
    def _get_empty_permissions(self) -> Dict:
        """Retorna permisos vacíos (sin acceso)"""
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
    
    def _get_base_table_permissions(self, user, table: Table) -> Dict:
        """Obtiene permisos base de tabla sin restricciones específicas de usuario"""
        # Usar el sistema de permisos existente de Baserow
        can_read = CoreHandler().check_permissions(
            user, 'database.table.read', table=table, raise_error=False
        )
        can_update = CoreHandler().check_permissions(
            user, 'database.table.update', table=table, raise_error=False  
        )
        
        all_field_ids = list(
            table.field_set.filter(trashed=False).values_list('id', flat=True)
        )
        
        return {
            'can_read': can_read,
            'can_create': can_update,  # Create requiere permisos de update
            'can_update': can_update,
            'can_delete': can_update,
            'can_manage_permissions': can_update,
            'visible_fields': all_field_ids,
            'has_row_filter': False, 
            'row_filter': {},
        }
    
    def _create_user_filtered_view(
        self, 
        user_rule: UserPermissionRule,
        base_view: Optional[View] = None
    ) -> UserFilteredView:
        """Crea una vista filtrada automáticamente para un usuario"""
        visible_fields = self._get_visible_fields_for_user(user_rule)
        
        return UserFilteredView.objects.create(
            table=user_rule.table,
            user=user_rule.user,
            name=f"My View - {user_rule.table.name}",
            base_view=base_view,
            user_filters=user_rule.row_filter,
            visible_fields=visible_fields,
            is_default=True
        )
    
    def filter_fields_by_user_permissions(
        self,
        fields: List[Field],
        user: User,
        table: Table
    ) -> List[Field]:
        """
        Filtra una lista de campos basándose en los permisos del usuario.
        Los campos con permiso 'hidden' serán excluidos de la lista.
        
        :param fields: Lista de campos a filtrar
        :param user: Usuario para el cual verificar permisos
        :param table: Tabla a la que pertenecen los campos
        :return: Lista de campos visibles para el usuario
        """
        # Si no hay autenticación, devolver todos los campos
        if not user or not user.is_authenticated:
            return fields
        
        # Obtener regla de permisos del usuario para esta tabla
        user_rule = self.get_user_permission_rule(table, user)
        
        # Si no hay regla específica, devolver todos los campos
        if not user_rule or not user_rule.is_active:
            return fields
        
        # Obtener permisos de campos para esta regla
        field_permissions = UserFieldPermission.objects.filter(
            user_rule=user_rule
        ).select_related('field')
        
        # Crear diccionario de field_id -> permission
        hidden_field_ids = set()
        for perm in field_permissions:
            if perm.permission == UserFieldPermission.PermissionChoices.HIDDEN:
                hidden_field_ids.add(perm.field_id)
        
        # Filtrar campos que no están ocultos
        visible_fields = [
            field for field in fields 
            if field.id not in hidden_field_ids
        ]
        
        return visible_fields