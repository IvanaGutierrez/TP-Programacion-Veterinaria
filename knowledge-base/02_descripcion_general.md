# Descripción General

## Stack tecnológico
| Capa | Tecnologías | Versión mínima | Uso en el proyecto |
|---|---|---|---|
| Lenguaje | Python | 3.12+ (3.13 en entorno) | Lenguaje base tipado |
| Framework Web | FastAPI | >= 0.111 | Enrutamiento HTTP, validación Pydantic v2, DI con `Depends`, lifespan |
| ORM / Modelos | SQLModel | >= 0.0.24 | Definición unificada de modelos de base de datos y esquemas |
| Driver DB / Motor | SQLAlchemy 2.0 (async), asyncpg | SQLAlchemy >= 2.0, asyncpg >= 0.30 | Motor asincrónico, `AsyncSession`, `expire_on_commit=False` |
| Base de datos | PostgreSQL | 16+ (PostgreSQL 18 en entorno) | Persistencia relacional, constraints (PK, FK, UNIQUE, CHECK) |
| Servidor ASGI | Uvicorn | Instalado vía `fastapi[standard]` | Servidor de desarrollo ASGI |
| Configuración | python-dotenv | >= 1.0 | Lectura de `DATABASE_URL` desde `.env` |

## Arquitectura general
La aplicación sigue un diseño modular por dominio vertical en `app/modules/`. Cada módulo encapsula sus modelos de datos (`models.py`), contratos de transferencia (`schemas.py`), lógica de negocio y transacciones (`service.py`) y controladores HTTP (`router.py`).

```text
               +-----------------------------+
               | Cliente HTTP / pruebas.http |
               +--------------+--------------+
                              |
                     FastAPI App (ASGI)
                              |
               +--------------+--------------+
               | Lifespan: Engine & Session  |
               +--------------+--------------+
                              |
          +-------------------+-------------------+
          |                   |                   |
    Router (HTTP)       Router (HTTP)       Router (HTTP)
       duenios             mascotas             turnos
          |                   |                   |
    Service (async)     Service (async)     Service (async)
          |                   |                   |
          +-------------------+-------------------+
                              |
                  SQLAlchemy AsyncSession
                  (expire_on_commit=False)
                              |
                    PostgreSQL Database
```

## Integraciones externas
| Servicio | Propósito | Tipo | Manejo de concurrencia |
|---|---|---|---|
| Laboratorio externo | Consulta de stock de vacunas mediante `cliente.py` (`time.sleep(1)`) | Biblioteca Python sincrónica provista por la cátedra | Delegación fuera del event loop con `asyncio.to_thread` o `run_in_threadpool` |

## API REST: Resumen de endpoints
| Método | Ruta | Recurso / Acción | Códigos HTTP |
|---|---|---|---|
| GET | `/health/live` | Health live (sin DB) | 200 |
| GET | `/health/ready` | Health ready (`SELECT 1`) | 200, 503 |
| POST | `/duenios/` | Alta de dueño | 201, 409, 422 |
| GET | `/duenios/{id}` | Obtener dueño con su ficha | 200, 404, 422 |
| PATCH | `/duenios/{id}` | Actualización parcial con `exclude_unset` | 200, 404, 409, 422 |
| DELETE | `/duenios/{id}` | Borrar dueño (`ON DELETE RESTRICT`) | 204, 404, 409 |
| POST | `/duenios/{id}/ficha` | Alta de ficha para dueño | 201, 404, 409 |
| GET | `/duenios/{id}/mascotas` | Mascotas pertenecientes a un dueño | 200, 404 |
| POST | `/mascotas/` | Alta de mascota con dueño existente | 201, 409, 422 |
| GET | `/mascotas/` | Listado paginado `{ items, total, page, size, pages }` | 200, 422 |
| GET | `/mascotas/{id}` | Obtener mascota con su dueño | 200, 404 |
| POST | `/practicas/` | Alta de práctica en catálogo | 201, 409, 422 |
| GET | `/practicas/` | Catálogo completo de prácticas | 200 |
| POST | `/turnos/` | Alta atómica de turno con prácticas congeladas | 201, 409, 422 |
| GET | `/turnos/{id}` | Detalle de turno con mascota y prácticas | 200, 404 |
| DELETE | `/turnos/{id}` | Borrar turno con cascada de prácticas en DB | 204, 404 |
| GET | `/laboratorio/stock/{vacuna}` | Consulta sincrónica no bloqueante de stock | 200 |
