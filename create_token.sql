-- Crear token de database para usuario test@test.com (id 4)
INSERT INTO database_token (key, name, user_id, workspace_id, created, handled_calls)
VALUES ('test_user_token_123456', 'Test Token', 4, 129, NOW(), 0);

-- Verificar
SELECT id, key, name, user_id, workspace_id FROM database_token WHERE user_id = 4;
