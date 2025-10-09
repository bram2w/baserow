# 🔍 CÓMO PROBAR EL FILTRO DE FILAS - Usuario Test

## Estado Actual

✅ **El filtro está FUNCIONANDO** - Ya fue probado exitosamente vía API
✅ **Patch aplicado** - row_filter_patch.py está activo en el backend
✅ **Regla configurada** - Usuario test@test.com tiene filtro: Coordinador = Anetth

## Problema Actual

Estás viendo TODOS los registros porque estás logueado como **cm@lasmananitas.com.mx** (ADMIN).
El filtro solo aplica al usuario **test@test.com**.

## 📋 Pasos para Ver el Filtro en Acción

### Opción 1: Iniciar Sesión como Test User en la UI

1. **Cerrar sesión** del usuario actual (cm@lasmananitas.com.mx)
   - Click en tu perfil (esquina superior derecha)
   - "Sign out" / "Cerrar sesión"

2. **Iniciar sesión con test@test.com**
   - Email: `test@test.com`
   - Password: `test123`

3. **Navegar a la tabla "Colabs"**
   - Workspace: "Las Mañanitas"
   - Database: "CRM" (o el que contenga la tabla)
   - Table: "Colabs"

4. **Resultado Esperado:**
   - ✅ Solo verás **3 registros** de 10:
     - ID 2: Carlos Rodríguez - Coordinador: Anetth
     - ID 6: Pedro Sánchez - Coordinador: Anetth
     - ID 10: Roberto Jiménez - Coordinador: Anetth
   - ❌ NO verás los otros 7 registros (con Brenda, Andrea, Hugo)

### Opción 2: Aplicar Filtro al Usuario Actual (cm@lasmananitas.com.mx)

Si quieres que TU usuario actual también vea el filtro, ejecuta:

\`\`\`sql
-- Crear regla de permiso para cm@lasmananitas.com.mx
INSERT INTO database_user_permission_rule (
    user_id, 
    table_id, 
    role, 
    is_active, 
    row_filter,
    created_on,
    updated_on
) VALUES (
    3,  -- ID del usuario cm@lasmananitas.com.mx
    738,  -- ID de la tabla Colabs
    'viewer',
    true,
    '{"filters": [{"field": 7105, "type": "equal", "value": 3045}], "filter_type": "AND"}',
    NOW(),
    NOW()
);
\`\`\`

## 🧪 Verificación que Ya Realizamos

✅ **Test API exitoso** (archivo test_row_filter.py):
- Token: test_user_token_123456
- Usuario: test@test.com
- Resultado: 3 registros visibles
- Log backend: "🔍 [ROW FILTER] Aplicando filtro para test@test.com en tabla Colabs"
- Log backend: "✅ [ROW FILTER] Filtro aplicado. Registros visibles: 3"

## 📊 Datos de Referencia

**Usuarios en el Sistema:**
- ID 1: dev@baserow.io (staff)
- ID 2: e2e@baserow.io (staff)
- ID 3: cm@lasmananitas.com.mx (ADMIN) ← **TU USUARIO ACTUAL**
- ID 4: test@test.com (MEMBER) ← **Usuario con filtro activo**

**Reglas de Permiso Activas:**
- Regla ID 1: test@test.com en tabla Colabs
  - Filtro: Coordinador (field 7105) = Anetth (value 3045)
  - Tipo: viewer
  - Estado: activa

**Registros en Tabla Colabs (10 total):**
- ✅ ID 2: Carlos - Anetth (VISIBLE para test user)
- ❌ ID 1: María - Brenda (OCULTO)
- ❌ ID 3: Ana - Andrea (OCULTO)
- ❌ ID 4: José - Hugo (OCULTO)
- ❌ ID 5: Laura - Brenda (OCULTO)
- ✅ ID 6: Pedro - Anetth (VISIBLE para test user)
- ❌ ID 7: Carmen - Andrea (OCULTO)
- ❌ ID 8: Miguel - Hugo (OCULTO)
- ❌ ID 9: Isabel - Brenda (OCULTO)
- ✅ ID 10: Roberto - Anetth (VISIBLE para test user)

## 🎯 Resultado Final Esperado

Cuando inicies sesión como **test@test.com**:
- Verás una tabla con solo **3 filas**
- La paginación mostrará "3 of 3" (no "10 of 10")
- Solo Anetth aparecerá en la columna Coordinador
- Los registros 1,3,4,5,7,8,9 estarán completamente ocultos

## ⚠️ Nota Importante

El filtro NO se aplica a:
- Usuarios ADMIN del workspace (como tu usuario actual)
- Usuarios sin reglas de permiso configuradas
- Tokens sin la tabla específica en sus permisos

Para que un usuario vea el filtro, DEBE tener una regla en la tabla `database_user_permission_rule`.
