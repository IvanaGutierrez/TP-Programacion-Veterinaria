# Visión y Objetivos

## Propósito del sistema
El sistema es una API asincrónica de gestión veterinaria barrial desarrollada con FastAPI, SQLModel y PostgreSQL para registrar dueños de mascotas, sus fichas de contacto, sus mascotas, un catálogo de prácticas médicas con precios vigentes y los turnos de atención con detalle de prácticas realizadas. El sistema asegura integridad referencial, cálculo atómico y congelamiento histórico de precios, delegando en la base de datos las comprobaciones y reglas de concurrencia e integridad.

## Objetivos por actor
| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| Recepcionista / Veterinario | Gestionar clientes (dueños), fichas de contacto, mascotas y reservar turnos de atención médica con prácticas asociadas | Consultar catálogo de prácticas, verificar disponibilidad de stock de vacunas con el laboratorio externo |
| Sistema / Administrador Técnico | Garantizar alta disponibilidad, monitoreo de salud operativa (live y ready) y consistencia transaccional sin bloqueos ni problemas N+1 | Recreación y siembra de base de datos (`reiniciar.py`), ejecución de pruebas automatizadas HTTP |

## Alcance v1.0
- **Ciclo de vida y salud**: Endpoints `/health/live` (sin tocar DB) y `/health/ready` (ejecuta `SELECT 1`, 503 en fallo). Inicialización de engine y sessionmaker en `lifespan` guardados en `app.state`.
- **Dueños y Ficha**: CRUD completo de dueños (POST, GET, PATCH parcial con `exclude_unset`, DELETE con `ON DELETE RESTRICT` si tiene mascotas). Alta y consulta de `FichaDuenio` (relación 1:1 estricta con `UNIQUE(duenio_id)`).
- **Mascotas**: Alta con asociación a dueño existente (`duenio_id`). Listado paginado con wrapper `{ items, total, page, size, pages }` (size default 20, rango 1-100, validación de página fuera de rango 422). Detalle de mascota con precarga de dueño.
- **Prácticas**: Catálogo de prácticas con nombre único y precio positivo (`CHECK precio > 0`, `NUMERIC(10,2)`). Alta y listado.
- **Turnos**: Alta atómica en una única transacción de turno con prácticas asociadas (`TurnoPractica`). Consulta de precios vigentes del catálogo, congelamiento de `precio_unitario` en la tabla intermedia y cálculo automático del `total` (`CHECK total >= 0`). Validación de al menos una práctica (422) y unicidad de práctica por turno (409 por PK compuesta). Borrado en cascada automático por base (`ON DELETE CASCADE` con `passive_deletes=True` en ORM).
- **Laboratorio**: Consulta de stock de vacunas (`GET /laboratorio/stock/{vacuna}`) que ejecuta la biblioteca bloqueante de la cátedra (`cliente.py`) fuera del event loop (`asyncio.to_thread` o `run_in_threadpool`) sin degradar la concurrencia.
- **Scripts y pruebas**: Script `reiniciar.py` con seed data mínimo obligatorio. Colección de pruebas `test/pruebas.http` para los 9 casos (C-01 a C-09).

## Fuera de alcance
- Autenticación y autorización (tokens, JWT, roles de usuario).
- Migraciones con Alembic (la base se genera y regenera mediante `SQLModel.metadata.create_all`).
- Colas de tareas en segundo plano (Celery, RQ, etc.).
- Patrones pesados de Repositorio o Unit of Work (la lógica reside directamente en los `service.py` que reciben `AsyncSession`).

## Métricas de éxito
- 100% de cumplimiento de los criterios de evaluación de la cátedra UTN Programación III.
- Cero excepciones `MissingGreenlet` mediante carga anticipada explícita (`joinedload` para relaciones a uno, `selectinload` para colecciones).
- Inexistencia de comprobaciones previas estilo "¿ya existe?" (captura de `IntegrityError` con rollback y retorno 409).
- Bloqueo cero en `/health/live` durante consultas concurrentes a `/laboratorio/stock/{vacuna}`.
