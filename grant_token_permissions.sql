-- Agregar permisos al token para la tabla 738
INSERT INTO database_tokenpermission (token_id, table_id, type) VALUES 
(2, 738, 'read');

-- Verificar
SELECT tp.*, dt.name as token_name 
FROM database_tokenpermission tp
JOIN database_token dt ON tp.token_id = dt.id
WHERE tp.token_id = 2;
