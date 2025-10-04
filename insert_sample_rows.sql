-- Script SQL para insertar 10 registros ficticios en la tabla Colabs

-- Insertar registros con coordinadores asignados
INSERT INTO database_table_738 (id, "order", field_7101, field_7102, field_7103, field_7104, field_7105, trashed, created_on, updated_on) VALUES
(1, '1.00000000000000000000', 'María González', 'María', '+52 777 123 4501', '@maria.gonzalez', 3044, false, NOW(), NOW()),
(2, '2.00000000000000000000', 'Carlos Rodríguez', 'Carlos', '+52 777 123 4502', '@carlos.rodriguez', 3045, false, NOW(), NOW()),
(3, '3.00000000000000000000', 'Ana Martínez', 'Ana', '+52 777 123 4503', '@ana.martinez', 3046, false, NOW(), NOW()),
(4, '4.00000000000000000000', 'José López', 'José', '+52 777 123 4504', '@jose.lopez', 3047, false, NOW(), NOW()),
(5, '5.00000000000000000000', 'Laura Hernández', 'Laura', '+52 777 123 4505', '@laura.hernandez', 3044, false, NOW(), NOW()),
(6, '6.00000000000000000000', 'Pedro Sánchez', 'Pedro', '+52 777 123 4506', '@pedro.sanchez', 3045, false, NOW(), NOW()),
(7, '7.00000000000000000000', 'Carmen Torres', 'Carmen', '+52 777 123 4507', '@carmen.torres', 3046, false, NOW(), NOW()),
(8, '8.00000000000000000000', 'Miguel Flores', 'Miguel', '+52 777 123 4508', '@miguel.flores', 3047, false, NOW(), NOW()),
(9, '9.00000000000000000000', 'Isabel Ramírez', 'Isabel', '+52 777 123 4509', '@isabel.ramirez', 3044, false, NOW(), NOW()),
(10, '10.00000000000000000000', 'Roberto Jiménez', 'Roberto', '+52 777 123 4510', '@roberto.jimenez', 3045, false, NOW(), NOW());

SELECT '✅ 10 registros creados exitosamente!' as resultado;
