# Arquitectura Propuesta

## Patrones Aplicados
| Patrón / Técnica | Dónde se usa | Justificación Técnica |
|---|---|---|
| Lifespan de Aplicación | `app/main.py` | Inicializa el motor asincrónico y `async_sessionmaker` en el inicio, los almacena en `app.state`, y cierra el motor limpiamente al apagar la app (Sección 1.9). |
| Inyección de Dependencias | `app/core/database.py` y routers | La sesión `AsyncSession` se inyecta por petición mediante `Depends(get_session)` con `expire_on_commit=False` para prevenir accesos post-commit fuera de sesión (Sección 4.5). |
| Separación Modelo vs DTO | `modules/<módulo>/models.py` vs `schemas.py` | Los modelos de tabla definen el esquema relacional. Los esquemas Pydantic validan entradas (`Create`, `Update`) y serializan salidas (`Read`), desacoplando el contrato HTTP de la base de datos (Sección 2.5). |
| Carga Anticipada Explícita | `service.py` en consultas de lectura | `joinedload` para relaciones a uno (`Duenio.ficha`, `Mascota.duenio`, `Turno.mascota`) y `selectinload` para colecciones (`Turno.turno_practicas`). Elimina el problema N+1 y previene excepciones `MissingGreenlet` (Sección 4.6). |
| Offloading a Thread Pool | `app/modules/laboratorio/` | `asyncio.to_thread` / `run_in_threadpool` para ejecutar código bloqueante sincrónico (`cliente.py`) en hilos secundarios, evitando congelar el event loop principal (Sección 3.6). |
| Delegación de Integridad en DB | `service.py` y PostgreSQL | En vez de comprobaciones previas vulnerables a condiciones de carrera, se delegan unicidad, foráneas y comprobaciones en PostgreSQL, capturando `IntegrityError` con rollback y código 409 (Sección 4.10). |

## Estructura de Directorios Canónica
```text
TP-Programacion-Veterinaria/
├── app/
│   ├── __init__.py
│   ├── main.py                     # Lifespan, app state, inclusión de routers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Settings con pydantic-settings / python-dotenv
│   │   └── database.py             # Engine asíncrono, sessionmaker, get_session
│   └── modules/
│       ├── __init__.py
│       ├── health/
│       │   ├── __init__.py
│       │   └── router.py           # GET /health/live, GET /health/ready
│       ├── duenios/
│       │   ├── __init__.py
│       │   ├── models.py           # Duenio, FichaDuenio
│       │   ├── schemas.py          # DuenioCreate, DuenioUpdate, DuenioRead, Ficha...
│       │   ├── service.py          # Lógica, captura IntegrityError, joinedload
│       │   └── router.py           # Endpoints /duenios/
│       ├── mascotas/
│       │   ├── __init__.py
│       │   ├── models.py           # Mascota
│       │   ├── schemas.py          # MascotaCreate, MascotaRead, MascotaPaginada
│       │   ├── service.py          # Lógica de paginación y precarga
│       │   └── router.py           # Endpoints /mascotas/
│       ├── practicas/
│       │   ├── __init__.py
│       │   ├── models.py           # Practica
│       │   ├── schemas.py          # PracticaCreate, PracticaRead
│       │   ├── service.py          # Catálogo y control de unicidad
│       │   └── router.py           # Endpoints /practicas/
│       ├── turnos/
│       │   ├── __init__.py
│       │   ├── models.py           # Turno, TurnoPractica
│       │   ├── schemas.py          # TurnoCreate, TurnoRead, TurnoPracticaRead
│       │   ├── service.py          # Alta atómica, congelamiento precios, borrado cascada
│       │   └── router.py           # Endpoints /turnos/
│       └── laboratorio/
│           ├── __init__.py
│           ├── cliente.py          # Código provisto por la cátedra (sincrónico)
│           ├── service.py          # Delegación no bloqueante (to_thread)
│           └── router.py           # GET /laboratorio/stock/{vacuna}
├── test/
│   └── pruebas.http                # Casos C-01 a C-09 documentados
├── reiniciar.py                    # Drop all, create all y carga seed data
├── requirements.txt                # Dependencias con versiones fijadas
├── .env.example                    # Plantilla de variables de entorno
├── .gitignore                      # Exclusiones de .env, cache y venv
└── README.md                       # Setup, respuestas teóricas y ejecución
```

## Variables de Entorno
| Variable | Descripción | Ejemplo | Sensible |
|---|---|---|---|
| `DATABASE_URL` | URL de conexión asincrónica a PostgreSQL (driver `postgresql+asyncpg`) | `postgresql+asyncpg://postgres:postgres@localhost:5432/veterinaria` | Sí |
| `ECHO_SQL` | Bandera para activar logging de sentencias SQL en consola (útil para caso C-07) | `True` o `False` | No |
