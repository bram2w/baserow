-- Ver todos los usuarios del sistema
SELECT id, email, first_name, is_staff, is_active 
FROM auth_user 
ORDER BY id;

-- Ver workspace memberships
SELECT wm.id, wm.user_id, u.email, w.name as workspace_name, wm.permissions
FROM core_workspaceuser wm
JOIN auth_user u ON wm.user_id = u.id
JOIN core_workspace w ON wm.workspace_id = w.id
WHERE w.id = 129
ORDER BY u.email;

-- Ver reglas de permisos actuales
SELECT 
    upr.id,
    upr.user_id,
    u.email,
    upr.table_id,
    t.name as table_name,
    upr.role,
    upr.is_active,
    upr.row_filter
FROM database_user_permission_rule upr
JOIN auth_user u ON upr.user_id = u.id
JOIN database_table t ON upr.table_id = t.id
ORDER BY u.email;
