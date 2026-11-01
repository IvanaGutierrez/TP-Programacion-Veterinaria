# Reglas de Negocio

Todas las reglas de negocio están codificadas bajo la convención `RN-XX` y garantizadas por el motor de base de datos o validaciones estrictas de esquemas Pydantic v2.

## Dominio: Dueños y Fichas (RN-DU)
- **RN-01**: *El email de un dueño es único*.
  - **Garante**: Constraint `UNIQUE` en la columna `duenio.email`.
  - **Manejo**: Si se intenta crear o actualizar con un email existente, el service atrapa `IntegrityError`, efectúa `await session.rollback()` y responde HTTP 409 ("El email ya se encuentra registrado").
- **RN-03**: *Un dueño tiene como máximo una ficha*.
  - **Garante**: Constraint `UNIQUE` en la columna `ficha_duenio.duenio_id`.
  - **Manejo**: Si se intenta crear una segunda ficha para el mismo dueño, la base rechaza por violación de unicidad y el service responde HTTP 409 ("El dueño ya posee una ficha registrada").
- **RN-08**: *No se puede borrar un dueño que tenga mascotas a su nombre*.
  - **Garante**: Clave foránea `mascota.duenio_id` con cláusula `ON DELETE RESTRICT`.
  - **Manejo**: Si se ejecuta `DELETE /duenios/{id}` y el dueño tiene mascotas asociadas, PostgreSQL rechaza la eliminación levantando una violación de integridad referencial. El service atrapa `IntegrityError`, hace rollback y responde HTTP 409 ("No se puede eliminar el dueño porque posee mascotas asociadas").

## Dominio: Prácticas Médicas (RN-PR)
- **RN-02**: *El nombre de una práctica es único*.
  - **Garante**: Constraint `UNIQUE` en la columna `practica.nombre`.
  - **Manejo**: La base rechaza nombres duplicados. El service responde HTTP 409 ("Ya existe una práctica con ese nombre").
- **RN-04**: *El precio de una práctica es mayor que cero*.
  - **Garante**: Doble control: validación de contrato Pydantic (`Field(gt=0)`) que arroja HTTP 422, y `CheckConstraint("precio > 0")` en PostgreSQL que rechaza escrituras directas (ej. UPDATE directo por SQL).

## Dominio: Turnos y Prácticas Asociadas (RN-TU)
- **RN-05**: *Un turno se reserva con sus prácticas: viajan dentro del cuerpo del alta del turno y debe tener al menos una*.
  - **Garante**: Esquema DTO `TurnoCreate` con campo `practicas: list[TurnoPracticaCreate] = Field(min_length=1)`. Si la lista viene vacía o nula, FastAPI/Pydantic rechaza con HTTP 422.
- **RN-06**: *El precio de cada práctica se copia del catálogo al reservar el turno, y el total lo calcula el servidor*.
  - **Garante**: En el DTO `TurnoCreate` no viajan ni precios ni total. El service busca las prácticas solicitadas en la base, congela el `precio_unitario` actual en cada registro `TurnoPractica`, suma los subtotales para determinar el `total` del `Turno`, y persiste todo atómicamente.
- **RN-07**: *Una misma práctica no aparece dos veces en un turno*.
  - **Garante**: Clave primaria compuesta `(turno_id, practica_id)` en la tabla `turno_practica`. Si se repite una práctica en la misma solicitud o turno, la base rechaza con `IntegrityError` y el service responde HTTP 409 ("Práctica duplicada en el turno").
- **RN-09**: *Al borrar un turno se borran sus prácticas*.
  - **Garante**: Clave foránea `turno_practica.turno_id` con regla `ON DELETE CASCADE`. En el modelo SQLModel de `Turno`, la relación hacia `turno_practicas` debe incluir `passive_deletes=True` para delegar el borrado íntegramente a PostgreSQL y evitar que SQLAlchemy intente emitir DELETEs manuales o desvincular con NULLs. Responde HTTP 204.

## Dominio: Transversal de Integridad y Concurrencia
- **RN-INT-01**: **Prohibición de SELECT previo estilo "¿ya existe?"**.
  - **Justificación**: Entre una consulta previa de verificación y la escritura efectiva existe una ventana de tiempo (race condition) en la que otra petición concurrente puede insertar el mismo registro. La única garantía real contra condiciones de carrera es la delegación en los constraints de PostgreSQL. El service escribe de inmediato dentro de la transacción y captura `IntegrityError` de SQLAlchemy/asyncpg.
- **RN-INT-02**: **Atomicidad "Todo o Nada"**.
  - Si una de las prácticas enviadas en el alta de turno no existe, o si la mascota no existe, la transacción completa es revertida (`rollback`), impidiendo estados inconsistentes o turnos huérfanos.
