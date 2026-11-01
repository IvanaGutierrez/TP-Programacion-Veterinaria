-- Caso C-08: Demostración de restricción CHECK en base de datos PostgreSQL
-- Al intentar actualizar una práctica con precio = 0 o negativo,
-- la base de datos PostgreSQL rechaza la operación debido al constraint:
-- CHECK (precio > 0) [chk_practica_precio_positivo].

UPDATE practica
SET precio = 0
WHERE id = 1;

-- Resultado esperado en PostgreSQL:
-- ERROR: el nuevo registro para la relación «practica» viola la restricción «check» «chk_practica_precio_positivo»
-- DETAIL: La fila que falla contiene (1, Consulta general, 0.00).
