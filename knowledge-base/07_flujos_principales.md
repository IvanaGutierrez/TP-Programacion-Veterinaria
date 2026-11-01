# Flujos Principales

Este documento detalla los flujos de ejecución extremo a extremo más críticos del sistema.

---

## Flujo 1: Alta Atómica de Turno con Congelamiento de Precios

**Disparador**: Operador envía `POST /turnos/` con `mascota_id`, `fecha`, `motivo` y `practicas: [{practica_id: 1}, {practica_id: 3}]`.  
**Actor**: Operador de Veterinaria  

### Pasos:
1. **Validación de Contrato**: FastAPI valida `TurnoCreate`. Si `practicas` está vacía, falla inmediatamente con HTTP 422.
2. **Revisión de Mascota**: El service comprueba la existencia de la mascota en la base. Si no existe, lanza 404 o 409 y cancela.
3. **Consulta de Precios Vigentes**: El service consulta en la tabla `practica` los registros correspondientes a los `practica_id` solicitados. Si alguna de las prácticas no existe en el catálogo, lanza excepción y aborta la transacción.
4. **Instanciación y Congelamiento**:
   - Se crea la entidad `Turno` asignando `mascota_id`, `fecha`, `motivo`.
   - Para cada práctica, se calcula el subtotal congelando `precio_unitario = practica.precio`.
   - Se suman los precios para fijar `Turno.total = sum(precios)`.
   - Se crean las instancias `TurnoPractica(practica_id=..., precio_unitario=...)`.
5. **Persistencia Atómica**:
   - Se agrega el turno y sus relaciones a la `session`.
   - Se ejecuta `await session.commit()`.
   - Si la base detecta una clave duplicada `(turno_id, practica_id)` o un fallo de integridad, se captura `IntegrityError`, se realiza `await session.rollback()` y se devuelve HTTP 409.
6. **Respuesta**: Se devuelve el turno con relaciones precargadas (`mascota` y `practicas`), HTTP 201.

### Diagrama de Secuencia (ASCII)
```text
Cliente                   Router / Service                PostgreSQL
   |                             |                             |
   |--- POST /turnos/ ---------->|                             |
   |    (sin precios ni total)   |                             |
   |                             |--- SELECT practicas ------->|
   |                             |<-- registros vigentes ------|
   |                             |                             |
   |                             | [Congela precio_unitario]   |
   |                             | [Calcula total = sum()]     |
   |                             |                             |
   |                             |--- BEGIN TRANSACTION ------>|
   |                             |--- INSERT turno ----------->|
   |                             |--- INSERT turno_practica -->|
   |                             |--- COMMIT ----------------->|
   |                             |<-- OK ----------------------|
   |                             |                             |
   |<-- HTTP 201 Created --------|                             |
   |    (total y precios fijos)  |                             |
```

---

## Flujo 2: Borrado con Cascada Automática (Turno) vs Restricción (Dueño)

### Escenario A: Borrado de Turno (`DELETE /turnos/{id}`)
1. Se busca el turno por ID. Si no existe, responde HTTP 404.
2. Se ejecuta `await session.delete(turno)` y `await session.commit()`.
3. Al tener `passive_deletes=True` en el ORM y `ON DELETE CASCADE` en la clave foránea `turno_practica.turno_id` de PostgreSQL, la base de datos elimina automáticamente todas las filas de `turno_practica` asociadas al turno.
4. SQLAlchemy no emite consultas individuales innecesarias.
5. Retorna HTTP 204 No Content (sin cuerpo).

### Escenario B: Intento de Borrado de Dueño con Mascotas (`DELETE /duenios/{id}`)
1. Se busca el dueño por ID. Si no existe, responde HTTP 404.
2. Se ejecuta `await session.delete(duenio)` y `await session.commit()`.
3. PostgreSQL detecta la existencia de filas en `mascota` asociadas por `mascota.duenio_id` cuya clave foránea declara `ON DELETE RESTRICT`.
4. PostgreSQL aborta la instrucción y arroja una violación de integridad referencial.
5. El service atrapa el `IntegrityError`, ejecuta `await session.rollback()` y devuelve HTTP 409 ("No se puede eliminar el dueño porque posee mascotas asociadas").

---

## Flujo 3: Ejecución No Bloqueante de Biblioteca Sincrónica

**Disparador**: Cliente envía `GET /laboratorio/stock/{vacuna}`.  
**Problema**: La biblioteca provista por la cátedra (`cliente.py`) tiene una función bloqueante `time.sleep(1)`. Si se ejecuta directamente dentro de una función `async def`, congela todo el bucle de eventos (event loop) de FastAPI durante 1 segundo, impidiendo que peticiones a `/health/live` se atiendan de inmediato.

### Mecanismo de resolución:
```text
Hilo Principal (Event Loop de asyncio)         Worker Thread Pool (to_thread)
               |                                            |
   GET /laboratorio/stock/antirrabica                       |
               |--- asyncio.to_thread(consultar_stock) ---->|
               |                                            |--- time.sleep(1) [bloquea hilo secundario]
   GET /health/live                                         |
               |---> responde 200 OK inmediatamente!        |
               |                                            |
               |<--- resultado (stock: 22) -----------------|
   Responde 200 OK con stock                                |
```

---

## Flujo 4: Paginación Segura de Mascotas

**Disparador**: Cliente envía `GET /mascotas/?page=3&size=10`.  
1. Valida que `size` esté en el rango 1 a 100 y `page >= 1` (Pydantic / Query parameters).
2. Consulta `COUNT(*)` sobre la tabla `mascota` (`total`).
3. Calcula `pages = ceil(total / size)` (o 1 si total es 0).
4. Comprueba si `page > pages`:
   - Si `total > 0` y `page > pages`: lanza `HTTPException(422, "Página fuera de rango")`.
   - Si `total == 0` y `page == 1`: no falla, retorna `items: []`, `total: 0`, `pages: 1`.
5. Ejecuta la consulta de registros con `offset = (page - 1) * size` y `limit = size`, precargando el dueño con `joinedload(Mascota.duenio)`.
6. Retorna el envoltorio `{ items, total, page, size, pages }` con HTTP 200.
