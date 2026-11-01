# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto Veterinaria (UTN Programación III - FastAPI y PostgreSQL).
> Cada change es atómico: un agente puede implementarlo en una sesión.
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. **Identificar el change** a implementar según el árbol de dependencias o camino crítico.
2. **Leer la documentación asociada** en `knowledge-base/` indicada en "Leer antes".
3. **Ejecutar la propuesta y especificación**: `/opsx:propose {change-id}-{nombre}`.
4. **Implementar y verificar**: `/opsx:apply {change-id}-{nombre}`.
5. **Archivar y sincronizar**: `/opsx:archive {change-id}-{nombre}` y marcar el checkbox en este documento.

---

## Árbol de dependencias

```text
C-01 foundation-setup
├── C-02 duenios-fichas-module
│   └── C-03 mascotas-module
│       └── C-05 turnos-module
├── C-04 practicas-module ───────┘
├── C-06 laboratorio-module
├── C-07 seed-script-reiniciar (requiere C-01..C-05)
└── C-08 testing-http-test-suite (requiere C-01..C-07)
    └── C-09 documentation-readme
```

### Paralelismo por fase

```text
GATE 0: Inicialización
  → C-01 foundation-setup                    [Agente A]

GATE 1: C-01 ✓ ← FORK
  → C-02 duenios-fichas-module               [Agente A]
  → C-04 practicas-module                    [Agente B]
  → C-06 laboratorio-module                  [Agente C]

GATE 2: C-02 ✓
  → C-03 mascotas-module                     [Agente A]

GATE 3: C-03 ✓ y C-04 ✓
  → C-05 turnos-module                       [Agente A]

GATE 4: C-02..C-06 ✓
  → C-07 seed-script-reiniciar               [Agente A]

GATE 5: C-07 ✓
  → C-08 testing-http-test-suite             [Agente B]

GATE 6: C-08 ✓
  → C-09 documentation-readme                [Agente A]
```

### Camino crítico (7 changes — mínimo irreducible)

```text
C-01 foundation-setup → C-02 duenios-fichas-module → C-03 mascotas-module → C-05 turnos-module → C-07 seed-script-reiniciar → C-08 testing-http-test-suite → C-09 documentation-readme
```

### Plan óptimo con 3 agentes

| Paso | Agente A (Core Domain) | Agente B (Catalog & Testing) | Agente C (Integraciones & Aux) |
|---|---|---|---|
| 1 | C-01 foundation-setup | — | — |
| 2 | C-02 duenios-fichas-module | C-04 practicas-module | C-06 laboratorio-module |
| 3 | C-03 mascotas-module | — | — |
| 4 | C-05 turnos-module | — | — |
| 5 | C-07 seed-script-reiniciar | C-08 testing-http-test-suite | — |
| 6 | C-09 documentation-readme | — | — |

---

## FASE 1 — Infraestructura y Configuración Base

### [C-01] `foundation-setup`
- **Estado**: `[x]` completado
- **Scope**:
  - `requirements.txt`: FastAPI, SQLModel, SQLAlchemy 2.0, asyncpg, python-dotenv, uvicorn.
  - `.env.example`: `DATABASE_URL` asincrónica (`postgresql+asyncpg://...`).
  - `.gitignore`: Exclusión de `.env`, `.venv`, `__pycache__`.
  - `app/core/config.py`: Carga tipada de configuración de entorno.
  - `app/core/database.py`: Creación de engine asíncrono, `async_sessionmaker(expire_on_commit=False)` y generador de dependencia `get_session`.
  - `app/main.py`: Lifespan de FastAPI gestionando el ciclo de vida del engine en `app.state`, registro de routers modulares.
  - `app/modules/health/router.py`: `GET /health/live` (sin DB, 200) y `GET /health/ready` (`SELECT 1`, 200/503).
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/01_vision_y_objetivos.md` §Alcance
  - `knowledge-base/02_descripcion_general.md` §Stack tecnológico
  - `knowledge-base/08_arquitectura_propuesta.md` §Lifespan e Inyección de Dependencias
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-02

---

## FASE 2 — Entidades y Catálogos Fundamentales

### [C-02] `duenios-fichas-module`
- **Estado**: `[x]` completado
- **Scope**:
  - `app/modules/duenios/models.py`: Modelo `Duenio` (id, nombre, email UNIQUE) y `FichaDuenio` (id, duenio_id FK UNIQUE, telefono, direccion). Relación 1 a 1 bidireccional con objeto directo en `Duenio.ficha`.
  - `app/modules/duenios/schemas.py`: DTOs `DuenioCreate`, `DuenioUpdate`, `DuenioRead`, `FichaCreate`, `FichaRead`.
  - `app/modules/duenios/service.py`: CRUD con captura directa de `IntegrityError` (sin SELECT previo), rollback y retorno 409. PATCH parcial con `.model_dump(exclude_unset=True)`. Carga anticipada `joinedload(Duenio.ficha)`. DELETE con captura de restricción `ON DELETE RESTRICT` (409).
  - `app/modules/duenios/router.py`: Endpoints `POST /duenios/` (201), `GET /duenios/{id}` (200/404/422), `PATCH /duenios/{id}` (200/404/409), `DELETE /duenios/{id}` (204/404/409), `POST /duenios/{id}/ficha` (201/404/409), `GET /duenios/{id}/mascotas` (200/404).
- **Dependencias**: `C-01`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §duenio y ficha_duenio
  - `knowledge-base/05_reglas_de_negocio.md` §RN-01, RN-03, RN-08
  - `knowledge-base/06_funcionalidades.md` §Épica 2
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-05, DD-06

### [C-03] `mascotas-module`
- **Estado**: `[x]` completado
- **Scope**:
  - `app/modules/mascotas/models.py`: Modelo `Mascota` (id, nombre, especie, duenio_id FK con ON DELETE RESTRICT e índice explícito). Relación con `Duenio` y `Turno`.
  - `app/modules/mascotas/schemas.py`: DTOs `MascotaCreate`, `MascotaRead`, `MascotaConDuenioRead`, y envoltorio de paginación `{ items, total, page, size, pages }`.
  - `app/modules/mascotas/service.py`: Alta con verificación de FK en base (captura `IntegrityError` 409). Listado paginado con `page` (default 1) y `size` (default 20, 1-100), cálculo de `pages = ceil(total/size)`, validación de `page > pages` retornando 422 salvo si `total == 0` y `page == 1`. Precarga con `joinedload(Mascota.duenio)`.
  - `app/modules/mascotas/router.py`: `POST /mascotas/` (201/409), `GET /mascotas/` (200/422), `GET /mascotas/{id}` (200/404).
- **Dependencias**: `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §mascota
  - `knowledge-base/05_reglas_de_negocio.md` §RN-08
  - `knowledge-base/06_funcionalidades.md` §Épica 3
  - `knowledge-base/07_flujos_principales.md` §Flujo 4

### [C-04] `practicas-module`
- **Estado**: `[x]` completado
- **Scope**:
  - `app/modules/practicas/models.py`: Modelo `Practica` (id, nombre UNIQUE, precio `NUMERIC(10,2)` con `CHECK (precio > 0)`). Decimal para montos monetarios.
  - `app/modules/practicas/schemas.py`: DTOs `PracticaCreate` con validación `gt=0`, `PracticaRead`.
  - `app/modules/practicas/service.py`: Alta de práctica capturando `IntegrityError` (409) si el nombre se repite. Consulta del catálogo completo.
  - `app/modules/practicas/router.py`: `POST /practicas/` (201/409/422), `GET /practicas/` (200).
- **Dependencias**: `C-01`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §practica
  - `knowledge-base/05_reglas_de_negocio.md` §RN-02, RN-04
  - `knowledge-base/06_funcionalidades.md` §Épica 4
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-01

---

## FASE 3 — Transacciones Complejas y Servicios Auxiliares

### [C-05] `turnos-module`
- **Estado**: `[x]` completado
- **Scope**:
  - `app/modules/turnos/models.py`: Modelo `Turno` (id, mascota_id FK con índice, fecha con zona horaria, motivo, total `NUMERIC(12,2)` con `CHECK (total >= 0)`). Relación `turno_practicas` con `cascade_delete=True, passive_deletes=True`.
  - Modelo `TurnoPractica`: Clave primaria compuesta `(turno_id, practica_id)`, `turno_id` FK con `ON DELETE CASCADE`, `practica_id` FK con índice explícito, `precio_unitario` (`NUMERIC(10,2)` con `CHECK (precio_unitario > 0)`).
  - `app/modules/turnos/schemas.py`: `TurnoCreate` con `practicas: list[TurnoPracticaCreate] = Field(min_length=1)` sin precios ni total. `TurnoRead`, `TurnoPracticaRead`.
  - `app/modules/turnos/service.py`: Alta atómica: valida existencia de mascota y prácticas, congela precio vigente del catálogo en `precio_unitario`, calcula `total = sum(precios)`, persiste atómicamente. Captura de duplicados de práctica en turno por PK compuesta (409). Carga anticipada `joinedload(Turno.mascota)` y `selectinload(Turno.turno_practicas).joinedload(TurnoPractica.practica)`. Borrado con delegación en `ON DELETE CASCADE` de PostgreSQL (204).
  - `app/modules/turnos/router.py`: `POST /turnos/` (201/409/422), `GET /turnos/{id}` (200/404), `DELETE /turnos/{id}` (204/404).
- **Dependencias**: `C-03`, `C-04`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §turno y turno_practica
  - `knowledge-base/05_reglas_de_negocio.md` §RN-05, RN-06, RN-07, RN-09
  - `knowledge-base/06_funcionalidades.md` §Épica 5
  - `knowledge-base/07_flujos_principales.md` §Flujo 1 y 2
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-01, DD-03, DD-04, DD-05

### [C-06] `laboratorio-module`
- **Estado**: `[x]` completado
- **Scope**:
  - `app/modules/laboratorio/cliente.py`: Inclusión exacta del código sincrónico provisto por la cátedra (`time.sleep(1)`).
  - `app/modules/laboratorio/service.py`: Función asincrónica que delega la invocación de `consultar_stock` a un worker thread mediante `asyncio.to_thread` o `fastapi.concurrency.run_in_threadpool`.
  - `app/modules/laboratorio/router.py`: Endpoint `GET /laboratorio/stock/{vacuna}` que responde `{"vacuna": ..., "stock": ...}` sin bloquear el event loop.
- **Dependencias**: `C-01`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/02_descripcion_general.md` §Integraciones externas
  - `knowledge-base/06_funcionalidades.md` §Épica 6
  - `knowledge-base/07_flujos_principales.md` §Flujo 3
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-07

---

## FASE 4 — Datos Semilla, Casos de Prueba y Documentación

### [C-07] `seed-script-reiniciar`
- **Estado**: `[x]` completado
- **Scope**:
  - `reiniciar.py`: Script asincrónico que:
    1. Importa todos los modelos de SQLModel para asegurar su registro en los metadatos.
    2. Conecta a la base y borra todas las tablas existentes (`SQLModel.metadata.drop_all`).
    3. Recrea las tablas con `SQLModel.metadata.create_all`.
    4. Inserta el seed data mínimo obligatorio:
       - 2 dueños: Juan Pérez con Ficha (tel: 11-4455-6677, dir: Av. Corrientes 1234) y María Gómez sin ficha.
       - 3 mascotas: Toby (perro, Juan), Milo (gato, Juan), Luna (perro, María).
       - 4 prácticas: Consulta general ($15000.00), Vacuna séxtuple ($18000.00), Vacuna antirrábica ($12000.00), Desparasitación ($8000.00).
       - 1 turno: Para Toby, motivo "Control y vacunación", con prácticas "Consulta general" ($15000.00) y "Vacuna antirrábica" ($12000.00), total $27000.00.
- **Dependencias**: `C-01`, `C-02`, `C-03`, `C-04`, `C-05`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Seed data inicial
  - `knowledge-base/08_arquitectura_propuesta.md`

### [C-08] `testing-http-test-suite`
- **Estado**: `[x]` completado
- **Scope**:
  - `test/pruebas.http`: Archivo HTTP con peticiones documentadas para los casos de prueba C-01 a C-09:
    - C-01: Parámetro no entero `/duenios/abc` -> 422.
    - C-02: Email o práctica duplicada -> 409 con mensaje propio.
    - C-03: Segunda ficha para el mismo dueño -> 409.
    - C-04: Mascota con dueño inexistente o turno con práctica inexistente -> 409/404 sin persistir nada.
    - C-05: Borrar dueño con mascotas (409) y borrar turno (204, cascada en DB).
    - C-06: Turno válido con dos prácticas (201 con precios y total calculado).
    - C-07: Detalle de turno con 1 y 3 prácticas (misma cantidad fija de queries en log `echo=True`).
    - C-08: UPDATE directo `UPDATE practica SET precio = 0` rechazado por CHECK de base (`test/c08_check_test.sql`).
    - C-09: Tres consultas concurrentes a `/laboratorio/stock/{vacuna}` y verificación de respuesta inmediata de `/health/live`.
- **Dependencias**: `C-07`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md`
  - `knowledge-base/06_funcionalidades.md`
  - `knowledge-base/07_flujos_principales.md`

### [C-09] `documentation-readme`
- **Estado**: `[x]` completado
- **Scope**:
  - `README.md` completo:
    - Guía de inicio rápido paso a paso: venv, instalación de `requirements.txt`, creación de `.env` a partir de `.env.example`, ejecución de `python reiniciar.py`, inicio de Uvicorn.
    - Explicación teórica precisa de por qué `turno_practica.turno_id` no requiere índice secundario en PostgreSQL (justificación mediante el índice B-tree de la clave primaria compuesta).
    - Evidencia de ejecución del caso C-07 (log de consola demostrando consultas fijas sin N+1).
- **Dependencias**: `C-08`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Índices de Claves Foráneas
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-04
