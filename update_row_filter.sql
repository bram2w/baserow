-- Actualizar regla de permisos con filtro de filas
-- Solo mostrar registros donde coordinador = Anetth (ID: 3045)

UPDATE database_user_permission_rule 
SET row_filter = '{"filter_type": "AND", "filters": [{"field": 7105, "type": "equal", "value": 3045}]}'::jsonb
WHERE id = 1;

-- Verificar el resultado
SELECT 
    upr.id,
    u.email,
    upr.table_id,
    upr.role,
    upr.row_filter
FROM database_user_permission_rule upr
JOIN auth_user u ON u.id = upr.user_id
WHERE upr.id = 1;
