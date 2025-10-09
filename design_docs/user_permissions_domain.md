# User Permissions & User Views - Diseño de Dominio

## 1. Modelo Conceptual

### 1.1 Roles de Usuario
```
admin      - Acceso completo, puede configurar permisos para otros
manager    - Puede ver/editar según configuración, otorgar permisos de nivel inferior
coordinator - Puede ver/editar según configuración, no otorgar permisos
viewer     - Solo lectura según configuración
```

### 1.2 Permisos a Nivel de Campo
```
read    - Puede ver el campo
write   - Puede ver y modificar el campo  
hidden  - Campo completamente oculto
```

### 1.3 Filtros a Nivel de Fila
Usando variables dinámicas del usuario:
- `{user.id}` - ID del usuario actual
- `{user.email}` - Email del usuario
- `{user.groups}` - Grupos/equipos del usuario
- `{user.department}` - Departamento del usuario

## 2. Modelos de Datos

### 2.1 UserPermissionRule
```python
class UserPermissionRule(models.Model):
    """Regla de permisos por usuario para una tabla específica"""
    table = models.ForeignKey('database.Table', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Admin'),
            ('manager', 'Manager'), 
            ('coordinator', 'Coordinator'),
            ('viewer', 'Viewer')
        ]
    )
    row_filter = models.JSONField(
        default=dict,
        help_text="Filtro JSON para limitar filas visibles usando variables de usuario"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['table', 'user']
```

### 2.2 UserFieldPermission
```python
class UserFieldPermission(models.Model):
    """Permisos específicos de campo para un usuario"""
    user_rule = models.ForeignKey(UserPermissionRule, on_delete=models.CASCADE)
    field = models.ForeignKey('database.Field', on_delete=models.CASCADE)
    permission = models.CharField(
        max_length=10,
        choices=[
            ('read', 'Read'),
            ('write', 'Write'),
            ('hidden', 'Hidden')
        ],
        default='read'
    )
    
    class Meta:
        unique_together = ['user_rule', 'field']
```

### 2.3 UserFilteredView
```python
class UserFilteredView(models.Model):
    """Vista personalizada para un usuario basada en sus permisos"""
    table = models.ForeignKey('database.Table', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    # Hereda de View existente
    base_view = models.ForeignKey('database.View', on_delete=models.CASCADE)
    # Filtros adicionales aplicados por permisos
    user_filters = models.JSONField(default=dict)
    visible_fields = models.JSONField(default=list)
    
    class Meta:
        unique_together = ['table', 'user']
```

## 3. Contratos de Permisos

### 3.1 UserPermissionManagerType
```python
class UserPermissionManagerType(PermissionManagerType):
    """Manager de permisos por usuario que extiende el sistema existente"""
    
    type = "user_permissions"
    
    def check_permissions(self, actor, operation, workspace=None, context=None):
        """Verifica permisos efectivos del usuario para una operación"""
        pass
        
    def get_effective_permissions(self, user, table, field=None):
        """Calcula permisos efectivos combinando rol base y reglas específicas"""
        pass
        
    def apply_row_filters(self, user, table, queryset):
        """Aplica filtros de fila usando variables del usuario"""
        pass
        
    def get_visible_fields(self, user, table):
        """Retorna campos visibles según permisos del usuario"""
        pass
```

### 3.2 Servicios de Dominio

#### UserPermissionService
```python
class UserPermissionService:
    """Servicio para gestionar reglas de permisos por usuario"""
    
    def grant_user_permission(self, table, user, role, row_filter=None):
        """Otorga permisos a un usuario para una tabla"""
        
    def set_field_permission(self, user_rule, field, permission):
        """Establece permiso específico de campo"""
        
    def revoke_user_permission(self, table, user):
        """Revoca todos los permisos de un usuario para una tabla"""
        
    def get_user_permissions_summary(self, user, table):
        """Obtiene resumen de todos los permisos de un usuario"""
```

#### UserViewService  
```python
class UserViewService:
    """Servicio para crear vistas filtradas por usuario"""
    
    def create_user_filtered_view(self, user, table, name, base_view=None):
        """Crea vista personalizada respetando permisos del usuario"""
        
    def get_user_view(self, user, table):
        """Obtiene la vista filtrada del usuario para una tabla"""
        
    def refresh_user_view(self, user, table):
        """Refresca vista cuando cambian los permisos"""
```

## 4. Variables de Usuario para Filtros

### 4.1 Context Variables
```python
USER_CONTEXT_VARS = {
    'user.id': lambda user: user.id,
    'user.email': lambda user: user.email, 
    'user.first_name': lambda user: user.first_name,
    'user.last_name': lambda user: user.last_name,
    'user.groups': lambda user: list(user.groups.values_list('name', flat=True)),
    'user.department': lambda user: getattr(user.profile, 'department', None),
    'user.is_staff': lambda user: user.is_staff,
    'user.date_joined': lambda user: user.date_joined,
}
```

### 4.2 Ejemplos de Filtros
```json
{
  "assigned_to": "{user.id}",
  "department": "{user.department}",
  "status__in": ["active", "pending"]
}
```

## 5. Integración con Sistema Existente

### 5.1 Compatibilidad
- Extiende `PermissionManagerType` existente
- Compatible con `BasicPermissionManager` y `RolePermissionManager`
- Respeta jerarquía de permisos: workspace → table → user
- No afecta operaciones existentes si no hay reglas de usuario

### 5.2 Precedencia de Permisos
1. **Workspace permissions** (más restrictivo)
2. **Role permissions** (Enterprise)  
3. **User permissions** (nueva capa)
4. **Default permissions** (más permisivo)

## 6. API Contracts

### 6.1 Endpoints REST
```
POST   /api/tables/{table_id}/user-permissions/
GET    /api/tables/{table_id}/user-permissions/
PATCH  /api/tables/{table_id}/user-permissions/{user_id}/
DELETE /api/tables/{table_id}/user-permissions/{user_id}/

POST   /api/tables/{table_id}/user-views/
GET    /api/tables/{table_id}/user-views/{user_id}/
```

### 6.2 Request/Response Schemas
```typescript
interface UserPermissionRequest {
  user_id: number;
  role: 'admin' | 'manager' | 'coordinator' | 'viewer';
  row_filter?: Record<string, any>;
  field_permissions?: Array<{
    field_id: number;
    permission: 'read' | 'write' | 'hidden';
  }>;
}

interface UserPermissionResponse {
  id: number;
  user: UserInfo;
  role: string;
  row_filter: Record<string, any>;
  field_permissions: FieldPermission[];
  effective_permissions: {
    can_read: boolean;
    can_write: boolean;
    can_delete: boolean;
    visible_fields: number[];
  };
}
```

## 7. Casos de Uso Principales

### 7.1 Escenario: Tabla "Eventos" de Marketing
- **Ana (Admin)**: Ve todos los eventos, puede configurar permisos
- **Bob (Manager)**: Ve eventos de su región, puede editar fechas y estado  
- **Carlos (Coordinator)**: Ve eventos donde aparece como coordinador, puede editar descripción
- **Diana (Viewer)**: Solo ve eventos públicos de su región, solo lectura

### 7.2 Configuración de Ejemplo
```python
# Ana otorga permisos a Bob para región "Norte"
grant_user_permission(
    table=eventos_table,
    user=bob,
    role='manager', 
    row_filter={'region': 'Norte'}
)

# Bob puede escribir en ciertos campos
set_field_permission(user_rule=bob_rule, field=fecha_field, permission='write')
set_field_permission(user_rule=bob_rule, field=presupuesto_field, permission='hidden')
```

## 8. Consideraciones Técnicas

### 8.1 Performance
- Índices en `(table, user)` para lookups rápidos
- Cache de permisos efectivos en Redis  
- Lazy loading de reglas complejas
- Optimización de queries con `select_related`

### 8.2 Security
- Validación de variables de usuario en filtros
- Sanitización de JSON filters
- Audit log de cambios de permisos
- Rate limiting en endpoints de configuración

### 8.3 Extensibilidad  
- Plugin system para nuevas variables de contexto
- Hooks para validación personalizada
- API para integraciones externas
- Backward compatibility garantizada