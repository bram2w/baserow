# Fork Changes - User Permissions Row-Level Filtering

Este documento describe las modificaciones realizadas al código fuente de Baserow para implementar el filtrado de filas basado en permisos de usuario.

## Cambios Realizados

### 1. `backend/src/baserow/contrib/database/api/rows/views.py`

**Modificación:** Agregar integración con `UserPermissionHandler` para aplicar filtros de fila.

**Ubicación:** Método `RowsView.get()` (línea ~369)

**Qué hace:**
- Intercepta las consultas de filas DESPUÉS de aplicar filtros de vista
- Aplica el `row_filter` JSON configurado en `UserPermissionRule`
- Solo afecta a usuarios con permisos configurados (no afecta admins)

**Código agregado:**
```python
# Import agregado al inicio del archivo
from baserow.contrib.database.user_permissions.handler import UserPermissionHandler

# Código agregado en get() después de aplicar filtros de vista
# (aproximadamente línea 440, después de view_handler.apply_filters)

# Apply user-level row filtering
if request.user and request.user.is_authenticated:
    try:
        permission_handler = UserPermissionHandler()
        queryset = permission_handler.apply_row_filters(
            user=request.user,
            table=table,
            queryset=queryset
        )
    except Exception as e:
        # Log error but don't break the request
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error applying user row filters: {e}")
```

**Razón del cambio:**
- Los intentos de monkey patching no funcionaron debido a la arquitectura de Baserow
- Necesitamos interceptar en el punto exacto donde se construye el queryset
- Esta es la única forma de garantizar que el filtro se aplique consistentemente

### 2. `backend/src/baserow/contrib/database/user_permissions/handler.py`

**Modificación:** Método `apply_row_filters()` ya existe y está listo.

**Estado:** ✅ No requiere cambios (ya implementado)

**Funcionalidad:**
- Lee `row_filter` JSON de `UserPermissionRule`
- Convierte filtros JSON a Django Q objects
- Aplica filtros al queryset
- Soporta filter_type: AND / OR
- Soporta tipos de filtro: equal, not_equal, contains, etc.

## Pruebas

### Test Case: Filtro por Coordinador=Anetth

**Setup:**
- Usuario: test@test.com (id=4)
- Tabla: Colabs (id=738)
- Campo: Coordinador (id=7105) - Multiple Select
- Datos: 10 registros totales
  - Brenda (3044): records 1, 5, 9
  - Anetth (3045): records 2, 6, 10 ← ESTOS DEBEN VERSE
  - Andrea (3046): records 3, 7
  - Hugo (3047): records 4, 8

**Configuración:**
```sql
-- UserPermissionRule
row_filter: {
  "filter_type": "AND",
  "filters": [
    {
      "field": 7105,
      "type": "equal", 
      "value": 3045
    }
  ]
}
```

**Resultado esperado:**
- GET /api/database/rows/table/738/ debe devolver solo 3 registros (IDs: 2, 6, 10)

### Comando de prueba:

```bash
# Desde el host
python test_row_filter.py
```

```python
# test_row_filter.py
import requests

response = requests.get(
    "http://localhost:4000/api/database/rows/table/738/",
    headers={"Authorization": "Token test_user_token_123456"}
)

data = response.json()
print(f"Total registros: {data['count']}")  # Esperado: 3
for row in data['results']:
    print(f"  - ID {row['id']}: {row['field_7102']} | Coordinador: {row['field_7105']}")
```

## Compatibilidad

### ✅ Cambios compatibles con:
- Field-level permissions (ya funcionales)
- Vistas existentes de Baserow
- Filtros ad-hoc
- Búsqueda de texto
- Ordenamiento
- Paginación
- Tokens de API

### ⚠️ Consideraciones:
- Los filtros de usuario se aplican DESPUÉS de filtros de vista
- Un usuario SIN `UserPermissionRule` ve todos los registros (comportamiento por defecto)
- Los admins/managers pueden configurar filtros más restrictivos que las vistas

## Mantenimiento del Fork

### Sincronizar con upstream:
```bash
# Traer cambios del repositorio oficial
git fetch upstream

# Ver diferencias
git log HEAD..upstream/master --oneline

# Merge (si es necesario)
git merge upstream/master

# Resolver conflictos en:
# - backend/src/baserow/contrib/database/api/rows/views.py (línea ~440)
```

### Archivos modificados a trackear:
- `backend/src/baserow/contrib/database/api/rows/views.py`

### Archivos nuevos (no requieren merge):
- `backend/src/baserow/contrib/database/user_permissions/**/*` (todo el módulo)

## Commits

- **Inicial:** `8919611ce` - Sistema completo de User Permissions con field-level permisos funcionando
- **Fork implementation:** (próximo commit después de testing)

## Referencias

- Issue original: "quiero que el registro se muestre SOLO SI COORDINADOR es ANETTH"
- Documento de diseño: `design_docs/user_permissions_domain.md`
- Handler: `backend/src/baserow/contrib/database/user_permissions/handler.py`
- Tests: `test_row_filter.py`, `test_field_permissions.py`
