-- Verificar tokens de usuario test@test.com
SELECT id, key, name, user_id 
FROM database_token 
WHERE user_id = 4;
