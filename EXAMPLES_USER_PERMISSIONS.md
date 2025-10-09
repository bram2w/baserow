# User Permissions API - Ejemplos de Uso

Este documento proporciona ejemplos prácticos de uso del sistema de permisos de usuario utilizando curl y escenarios del mundo real.

## Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Escenario: Gestión de Eventos](#escenario-gestión-de-eventos)
3. [Ejemplos de API](#ejemplos-de-api)
4. [Casos de Uso Comunes](#casos-de-uso-comunes)

---

## Configuración Inicial

### Autenticación

Todos los ejemplos requieren autenticación. Obtén tu token JWT:

```bash
curl -X POST http://localhost:8000/api/user/token-auth/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your_password"
  }'
```

Respuesta:
```json
{
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Admin"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Usa el token en todas las peticiones:
```bash
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## Escenario: Gestión de Eventos

### Contexto del Negocio

Tienes una tabla **"Eventos"** con los siguientes campos:
- `nombre` (text): Nombre del evento
- `fecha` (date): Fecha del evento
- `ubicacion` (text): Lugar del evento
- `organizador` (single_select): Departamento organizador (Marketing, Ventas, IT)
- `presupuesto` (number): Presupuesto asignado
- `estado` (single_select): Estado (Planificado, En curso, Completado)
- `notas_internas` (long_text): Notas confidenciales

### Roles y Permisos

1. **Coordinadores de Marketing**: 
   - Solo ven eventos de Marketing
   - Pueden crear y leer, pero no modificar ni eliminar
   - No ven presupuesto ni notas internas

2. **Gerentes de Ventas**:
   - Ven eventos de Ventas
   - Pueden crear, leer y actualizar
   - Ven presupuesto pero no notas internas

3. **Administrador de Eventos**:
   - Ve todos los eventos
   - Acceso completo (CRUD)
   - Ve todos los campos

---

## Ejemplos de API

### 1. Listar Permisos Actuales

```bash
curl -X GET "http://localhost:8000/api/database/tables/42/user-permissions/" \
  -H "Authorization: JWT $TOKEN"
```

**Respuesta:**
```json
[
  {
    "user": {
      "id": 5,
      "email": "maria@company.com",
      "first_name": "María"
    },
    "role": "coordinator",
    "row_filter": {
      "organizador": "{user.department}"
    },
    "field_permissions": [
      {
        "field": {"id": 101, "name": "presupuesto"},
        "permission": "hidden"
      },
      {
        "field": {"id": 102, "name": "notas_internas"},
        "permission": "hidden"
      }
    ],
    "effective_permissions": {
      "can_read": true,
      "can_create": true,
      "can_update": false,
      "can_delete": false
    },
    "created_at": "2025-10-01T10:00:00Z",
    "updated_at": "2025-10-01T10:00:00Z",
    "is_active": true
  }
]
```

### 2. Crear Permiso para Coordinador de Marketing

```bash
curl -X POST "http://localhost:8000/api/database/tables/42/user-permissions/" \
  -H "Authorization: JWT $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 5,
    "role": "coordinator",
    "row_filter": {
      "organizador": "Marketing"
    },
    "field_permissions": [
      {
        "field_id": 101,
        "permission": "hidden"
      },
      {
        "field_id": 102,
        "permission": "hidden"
      }
    ]
  }'
```

**Respuesta:** 201 Created
```json
{
  "user": {
    "id": 5,
    "email": "maria@company.com",
    "first_name": "María"
  },
  "role": "coordinator",
  "row_filter": {
    "organizador": "Marketing"
  },
  "field_permissions": [
    {
      "field": {"id": 101, "name": "presupuesto"},
      "permission": "hidden"
    },
    {
      "field": {"id": 102, "name": "notas_internas"},
      "permission": "hidden"
    }
  ],
  "effective_permissions": {
    "can_read": true,
    "can_create": true,
    "can_update": false,
    "can_delete": false
  }
}
```

### 3. Crear Permiso para Gerente de Ventas

```bash
curl -X POST "http://localhost:8000/api/database/tables/42/user-permissions/" \
  -H "Authorization: JWT $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 8,
    "role": "manager",
    "row_filter": {
      "organizador": "Ventas",
      "estado": ["Planificado", "En curso"]
    },
    "field_permissions": [
      {
        "field_id": 101,
        "permission": "read"
      },
      {
        "field_id": 102,
        "permission": "hidden"
      }
    ]
  }'
```

### 4. Actualizar Permisos Existentes

```bash
curl -X PATCH "http://localhost:8000/api/database/tables/42/user-permissions/5/" \
  -H "Authorization: JWT $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "manager",
    "field_permissions": [
      {
        "field_id": 101,
        "permission": "read"
      }
    ]
  }'
```

### 5. Obtener Resumen de Permisos de Usuario

```bash
curl -X GET "http://localhost:8000/api/database/tables/42/user-permissions/5/summary/" \
  -H "Authorization: JWT $TOKEN"
```

**Respuesta:**
```json
{
  "user": {
    "id": 5,
    "email": "maria@company.com"
  },
  "table": {
    "id": 42,
    "name": "Eventos"
  },
  "has_permissions": true,
  "rule": {
    "role": "coordinator",
    "row_filter": {
      "organizador": "Marketing"
    }
  },
  "field_permissions": [
    {
      "field": {"id": 101, "name": "presupuesto"},
      "permission": "hidden"
    }
  ],
  "effective_permissions": {
    "can_read": true,
    "can_create": true,
    "can_update": false,
    "can_delete": false
  },
  "visible_fields": [1, 2, 3, 4, 6],
  "row_count": 15
}
```

### 6. Obtener Vista Filtrada del Usuario

```bash
curl -X GET "http://localhost:8000/api/database/tables/42/user-permissions/filtered-view/" \
  -H "Authorization: JWT $TOKEN"
```

**Respuesta:**
```json
{
  "user": {
    "id": 5,
    "email": "maria@company.com"
  },
  "table": {
    "id": 42,
    "name": "Eventos"
  },
  "user_filters": {
    "organizador": "Marketing"
  },
  "visible_fields": [1, 2, 3, 4, 6],
  "hidden_fields": [101, 102],
  "is_default": true,
  "created_at": "2025-10-01T10:00:00Z"
}
```

### 7. Refrescar Vista Filtrada

```bash
curl -X POST "http://localhost:8000/api/database/tables/42/user-permissions/filtered-view/" \
  -H "Authorization: JWT $TOKEN"
```

### 8. Consultar Audit Log

```bash
curl -X GET "http://localhost:8000/api/database/tables/42/user-permissions/audit-logs/?page_size=10" \
  -H "Authorization: JWT $TOKEN"
```

**Respuesta:**
```json
[
  {
    "id": 123,
    "table": {"id": 42, "name": "Eventos"},
    "target_user": {
      "id": 5,
      "email": "maria@company.com",
      "first_name": "María"
    },
    "actor_user": {
      "id": 1,
      "email": "admin@example.com",
      "first_name": "Admin"
    },
    "action": "granted",
    "details": {
      "role": "coordinator",
      "row_filter": {"organizador": "Marketing"}
    },
    "created_at": "2025-10-01T10:00:00Z"
  },
  {
    "id": 124,
    "action": "modified",
    "details": {
      "role": "manager",
      "previous_role": "coordinator"
    },
    "created_at": "2025-10-02T14:30:00Z"
  }
]
```

### 9. Revocar Permisos

```bash
curl -X DELETE "http://localhost:8000/api/database/tables/42/user-permissions/5/" \
  -H "Authorization: JWT $TOKEN"
```

**Respuesta:** 204 No Content

---

## Casos de Uso Comunes

### Caso 1: Acceso Temporal a Contratista

**Escenario:** Dar acceso de solo lectura a un contratista externo por 30 días.

```bash
# Crear permiso de viewer
curl -X POST "http://localhost:8000/api/database/tables/42/user-permissions/" \
  -H "Authorization: JWT $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 15,
    "role": "viewer",
    "row_filter": {
      "estado": "Completado"
    },
    "field_permissions": [
      {
        "field_id": 101,
        "permission": "hidden"
      },
      {
        "field_id": 102,
        "permission": "hidden"
      }
    ]
  }'

# Después de 30 días, revocar
curl -X DELETE "http://localhost:8000/api/database/tables/42/user-permissions/15/" \
  -H "Authorization: JWT $TOKEN"
```

### Caso 2: Filtros Dinámicos por Usuario

**Escenario:** Cada usuario solo ve eventos de su departamento.

```bash
curl -X POST "http://localhost:8000/api/database/tables/42/user-permissions/" \
  -H "Authorization: JWT $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 10,
    "role": "coordinator",
    "row_filter": {
      "organizador": "{user.department}"
    }
  }'
```

El sistema resolverá `{user.department}` automáticamente usando el perfil del usuario.

### Caso 3: Escalado de Permisos

**Escenario:** Promover un coordinador a manager.

```bash
curl -X PATCH "http://localhost:8000/api/database/tables/42/user-permissions/5/" \
  -H "Authorization: JWT $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "manager"
  }'
```

### Caso 4: Permisos Granulares por Campo

**Escenario:** Permitir que el usuario vea presupuesto pero no lo edite.

```bash
curl -X PATCH "http://localhost:8000/api/database/tables/42/user-permissions/5/" \
  -H "Authorization: JWT $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "field_permissions": [
      {
        "field_id": 101,
        "permission": "read"
      }
    ]
  }'
```

### Caso 5: Auditoría de Cambios

**Escenario:** Revisar quién modificó permisos en el último mes.

```bash
curl -X GET "http://localhost:8000/api/database/tables/42/user-permissions/audit-logs/?created_at__gte=2025-09-01" \
  -H "Authorization: JWT $TOKEN"
```

---

## Códigos de Error Comunes

### 400 Bad Request
```json
{
  "error": "ERROR_USER_PERMISSION_RULE_ALREADY_EXISTS",
  "detail": "A permission rule already exists for this user and table"
}
```

### 403 Forbidden
```json
{
  "error": "ERROR_CANNOT_MANAGE_USER_PERMISSIONS",
  "detail": "You do not have permission to manage user permissions for this table"
}
```

### 404 Not Found
```json
{
  "error": "ERROR_USER_PERMISSION_RULE_DOES_NOT_EXIST",
  "detail": "The requested permission rule does not exist"
}
```

---

## Variables de Filtro Dinámico

El sistema soporta las siguientes variables dinámicas en `row_filter`:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `{user.id}` | ID del usuario | `"owner_id": "{user.id}"` |
| `{user.email}` | Email del usuario | `"email": "{user.email}"` |
| `{user.department}` | Departamento | `"departamento": "{user.department}"` |
| `{user.role}` | Rol del usuario | `"rol": "{user.role}"` |
| `{user.team}` | Equipo del usuario | `"equipo": "{user.team}"` |

Las variables se resuelven en tiempo de ejecución para cada petición.

---

## Mejores Prácticas

1. **Principio de Menor Privilegio**: Comienza con rol `viewer` y escala según necesidad
2. **Auditoría Regular**: Revisa audit logs mensualmente
3. **Filtros Dinámicos**: Usa `{user.*}` para escalabilidad
4. **Campos Sensibles**: Marca como `hidden` datos confidenciales
5. **Documentación**: Documenta la lógica de permisos en tu equipo
6. **Testing**: Prueba permisos antes de aplicar en producción
7. **Revocación**: Revoca acceso cuando usuarios cambian de rol

---

## Integración con CI/CD

### Script de Migración de Permisos

```python
# migrate_permissions.py
import requests

BASE_URL = "http://localhost:8000/api"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"JWT {TOKEN}",
    "Content-Type": "application/json"
}

# Definir permisos por departamento
DEPARTMENT_PERMISSIONS = {
    "marketing": {
        "role": "coordinator",
        "row_filter": {"organizador": "Marketing"},
        "hidden_fields": [101, 102]
    },
    "sales": {
        "role": "manager",
        "row_filter": {"organizador": "Ventas"},
        "hidden_fields": [102]
    }
}

def apply_permissions(table_id, users):
    for user in users:
        dept_config = DEPARTMENT_PERMISSIONS.get(user['department'])
        if not dept_config:
            continue
            
        payload = {
            "user_id": user['id'],
            "role": dept_config['role'],
            "row_filter": dept_config['row_filter'],
            "field_permissions": [
                {"field_id": fid, "permission": "hidden"}
                for fid in dept_config['hidden_fields']
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/database/tables/{table_id}/user-permissions/",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 201:
            print(f"✓ Permissions created for {user['email']}")
        else:
            print(f"✗ Failed for {user['email']}: {response.text}")

if __name__ == "__main__":
    # Obtener usuarios del workspace
    users_response = requests.get(f"{BASE_URL}/workspaces/1/users/", headers=headers)
    users = users_response.json()
    
    # Aplicar permisos
    apply_permissions(table_id=42, users=users)
```

---

**Nota:** Todos los ejemplos asumen que el servidor está corriendo en `http://localhost:8000`. Ajusta las URLs según tu configuración.