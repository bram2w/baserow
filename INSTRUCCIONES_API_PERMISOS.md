# 🔐 Instrucciones para Gestionar Permisos de Usuario via API

## Problema Actual
La interfaz web de User Permissions tiene problemas de routing en el frontend. Mientras se soluciona, puedes gestionar permisos completamente via API REST.

## Tu Tabla
- **Database ID**: 191 (CRM - Las Mañanitas)
- **Table ID**: 735
- **URL de la tabla**: http://localhost:4000/database/191/table/735/3289

---

## Paso 1: Obtener Token de Autenticación

```powershell
# Reemplaza con tu usuario y contraseña de Baserow
$credentials = @{
    username = 'tu_email@ejemplo.com'
    password = 'tu_contraseña'
} | ConvertTo-Json

$response = Invoke-RestMethod -Method Post -Uri "http://localhost:4000/api/user/token-auth/" -Body $credentials -ContentType "application/json"
$token = $response.token
Write-Host "Token: $token"
```

---

## Paso 2: Listar Permisos Existentes

```powershell
$headers = @{
    Authorization = "JWT $token"
}

$permisos = Invoke-RestMethod -Method Get -Uri "http://localhost:4000/api/database/tables/735/user-permissions/" -Headers $headers
$permisos | ConvertTo-Json -Depth 10
```

---

## Paso 3: Obtener Lista de Usuarios

```powershell
# Primero necesitas obtener los IDs de los usuarios del workspace
$workspace_id = 191  # ID del workspace CRM - Las Mañanitas

# Listar usuarios (necesitas permisos de admin)
$usuarios = Invoke-RestMethod -Method Get -Uri "http://localhost:4000/api/workspaces/$workspace_id/users/" -Headers $headers
$usuarios | ConvertTo-Json -Depth 5
```

---

## Paso 4: Obtener IDs de Campos de la Tabla

```powershell
$campos = Invoke-RestMethod -Method Get -Uri "http://localhost:4000/api/database/fields/table/735/" -Headers $headers
$campos | ForEach-Object { Write-Host "Campo ID: $($_.id) | Nombre: $($_.name) | Tipo: $($_.type)" }
```

---

## Paso 5: Crear Regla de Permisos para un Usuario

### Ejemplo 1: Usuario VIEWER (solo lectura)

```powershell
$nuevaRegla = @{
    user_id = 2  # Reemplaza con el ID del usuario
    role = "viewer"
    row_filter = @{}  # Sin filtro de filas (ve todo)
    is_active = $true
    field_permissions = @(
        @{
            field_id = 10  # ID del campo
            permission = "read"  # read, write, o hidden
        },
        @{
            field_id = 11
            permission = "hidden"  # Este campo no lo ve
        }
    )
} | ConvertTo-Json -Depth 10

$resultado = Invoke-RestMethod -Method Post -Uri "http://localhost:4000/api/database/tables/735/user-permissions/" -Headers $headers -Body $nuevaRegla -ContentType "application/json"
$resultado | ConvertTo-Json -Depth 10
```

### Ejemplo 2: Usuario COORDINATOR con filtro de filas

```powershell
$nuevaRegla = @{
    user_id = 3
    role = "coordinator"
    row_filter = @{
        "assigned_to" = "{user.id}"  # Solo ve sus propios registros
        "department" = "{user.department}"  # Solo su departamento
    }
    is_active = $true
    field_permissions = @(
        @{
            field_id = 10
            permission = "write"  # Puede editar
        },
        @{
            field_id = 11
            permission = "read"  # Solo lectura
        }
    )
} | ConvertTo-Json -Depth 10

$resultado = Invoke-RestMethod -Method Post -Uri "http://localhost:4000/api/database/tables/735/user-permissions/" -Headers $headers -Body $nuevaRegla -ContentType "application/json"
$resultado | ConvertTo-Json -Depth 10
```

---

## Paso 6: Actualizar una Regla Existente

```powershell
$rule_id = 1  # ID de la regla a actualizar

$actualizacion = @{
    role = "manager"
    is_active = $true
} | ConvertTo-Json

$resultado = Invoke-RestMethod -Method Patch -Uri "http://localhost:4000/api/database/tables/735/user-permissions/$rule_id/" -Headers $headers -Body $actualizacion -ContentType "application/json"
$resultado | ConvertTo-Json -Depth 10
```

---

## Paso 7: Ver Resumen de una Regla

```powershell
$rule_id = 1

$resumen = Invoke-RestMethod -Method Get -Uri "http://localhost:4000/api/database/tables/735/user-permissions/$rule_id/summary/" -Headers $headers
$resumen | ConvertTo-Json -Depth 10
```

---

## Paso 8: Eliminar una Regla de Permisos

```powershell
$rule_id = 1

Invoke-RestMethod -Method Delete -Uri "http://localhost:4000/api/database/tables/735/user-permissions/$rule_id/" -Headers $headers
Write-Host "Regla eliminada exitosamente"
```

---

## Roles Disponibles

| Rol | Permisos |
|-----|----------|
| **viewer** | Solo lectura, sin edición |
| **coordinator** | Puede editar registros permitidos |
| **manager** | Gestiona registros y campos |
| **admin** | Control total |

---

## Permisos de Campo

| Permiso | Descripción |
|---------|-------------|
| **read** | Solo lectura |
| **write** | Lectura y escritura |
| **hidden** | Campo oculto (no visible) |

---

## Variables Dinámicas en Filtros

Puedes usar estas variables en `row_filter`:

- `{user.id}` - ID del usuario actual
- `{user.email}` - Email del usuario
- `{user.username}` - Nombre de usuario
- `{user.first_name}` - Nombre
- `{user.last_name}` - Apellido

**Ejemplo práctico:**
```json
{
  "row_filter": {
    "assigned_to": "{user.id}",
    "status": "active"
  }
}
```
Esto hace que el usuario solo vea registros donde `assigned_to` = su ID y `status` = "active".

---

## Script Completo de Ejemplo

```powershell
# 1. Autenticarse
$credentials = @{
    username = 'admin@ejemplo.com'
    password = 'mi_password'
} | ConvertTo-Json

$response = Invoke-RestMethod -Method Post -Uri "http://localhost:4000/api/user/token-auth/" -Body $credentials -ContentType "application/json"
$token = $response.token
$headers = @{ Authorization = "JWT $token" }

# 2. Listar campos de la tabla
Write-Host "`n=== CAMPOS DE LA TABLA ===" -ForegroundColor Green
$campos = Invoke-RestMethod -Method Get -Uri "http://localhost:4000/api/database/fields/table/735/" -Headers $headers
$campos | ForEach-Object { Write-Host "Campo ID: $($_.id) | Nombre: $($_.name)" }

# 3. Crear regla de permisos
Write-Host "`n=== CREANDO REGLA DE PERMISOS ===" -ForegroundColor Green
$nuevaRegla = @{
    user_id = 2
    role = "viewer"
    row_filter = @{}
    is_active = $true
    field_permissions = @(
        @{ field_id = $campos[0].id; permission = "read" }
    )
} | ConvertTo-Json -Depth 10

$resultado = Invoke-RestMethod -Method Post -Uri "http://localhost:4000/api/database/tables/735/user-permissions/" -Headers $headers -Body $nuevaRegla -ContentType "application/json"
Write-Host "Regla creada con ID: $($resultado.id)" -ForegroundColor Yellow

# 4. Listar todas las reglas
Write-Host "`n=== REGLAS EXISTENTES ===" -ForegroundColor Green
$reglas = Invoke-RestMethod -Method Get -Uri "http://localhost:4000/api/database/tables/735/user-permissions/" -Headers $headers
$reglas.results | ForEach-Object { 
    Write-Host "Regla ID: $($_.id) | Usuario: $($_.user.username) | Rol: $($_.role) | Activa: $($_.is_active)"
}
```

---

## Notas Importantes

1. **Backend está funcional**: Todas las migraciones se aplicaron correctamente y los endpoints funcionan
2. **Frontend tiene problemas**: La página de UI tiene problemas de routing que deben corregirse
3. **API es la solución temporal**: Mientras se corrige el frontend, usa la API REST
4. **Documentación completa**: Ver `EXAMPLES_USER_PERMISSIONS.md` para más ejemplos

---

## Próximos Pasos para Corregir el Frontend

1. Revisar el sistema de routing de Nuxt en Baserow
2. Posiblemente necesitar registrar la ruta manualmente en el plugin
3. O mover `userPermissions.vue` fuera de `pages/table/` a `pages/`
4. Verificar que los componentes Vue se carguen correctamente

---

## Soporte

Si tienes problemas con la API, revisa:
- Logs del backend: `docker logs baserow-backend-1`
- Estado de las tablas: Ya verificado ✅
- Migraciones aplicadas: Ya aplicado ✅
- Modelos Django: Ya funcionales ✅
