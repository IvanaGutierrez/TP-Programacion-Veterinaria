# AGENTS.md — Reglas y Guía de Arquitectura para Agentes

> Proyecto: Veterinaria API (FastAPI + SQLModel + PostgreSQL) — UTN Programación III.

## Mapa de Navegación
- **Documentación Canónica**: `knowledge-base/` (10 archivos canónicos: visión, modelo de datos, reglas de negocio, flujos, arquitectura, decisiones).
- **Roadmap de Changes**: `CHANGES.md`.
- **Registro de Skills**: `.atl/skill-registry.md`.

## Reglas Duras del Proyecto (No Negociables)

1. **Ciclo de vida y conexión**:
   - El motor asincrónico y `async_sessionmaker` se crean en el `lifespan` de FastAPI y se guardan en `app.state`.
   - La sesión llega a cada handler con `Depends(get_session)` con `expire_on_commit=False`.
   - `DATABASE_URL` se lee exclusivamente desde `.env` usando `python-dotenv` / `pydantic-settings`.

2. **Manejo monetario**:
   - Todo campo o cálculo de dinero DEBE usar `Decimal`, NUNCA `float`.
   - Base de datos: `Numeric(10,2)` y `Numeric(12,2)`.

3. **Manejo de integridad y concurrencia**:
   - PROHIBIDO hacer SELECT previo estilo "¿ya existe?".
   - Escribir directamente en base y capturar `IntegrityError` en `service.py`, hacer `await session.rollback()` y lanzar `HTTPException(409, detail=...)`.

4. **Carga anticipada explícita (Anti N+1 y Anti MissingGreenlet)**:
   - Toda lectura que devuelva relaciones debe precargarse explícitamente: `joinedload` para relaciones "a uno" y `selectinload` para colecciones.
   - Cero lazy loading.

5. **Asincronía sin bloqueos**:
   - Todos los handlers deben ser `async def`.
   - La función bloqueante `consultar_stock` de `app/modules/laboratorio/cliente.py` debe ejecutarse fuera del event loop usando `asyncio.to_thread(...)`.

6. **Relaciones y borrados en cascada / restricción**:
   - `Duenio` -> `mascota`: `ON DELETE RESTRICT` en PostgreSQL (borrar dueño con mascotas arroja 409).
   - `Turno` -> `turno_practica`: `ON DELETE CASCADE` en PostgreSQL y `passive_deletes=True` en la relación ORM de `Turno` (borrar turno borra sus prácticas con 204).
   - Clave primaria compuesta en `turno_practica (turno_id, practica_id)`. `turno_id` no lleva índice explícito; `practica_id` sí.

7. **Paginación en mascotas**:
   - Retornar `{ items, total, page, size, pages }`.
   - Si `page > pages` y `total > 0`, responder HTTP 422. Si `total == 0` y `page == 1`, responder 200 con `items: []`.
