# Veterinaria — Trabajo Práctico con FastAPI y PostgreSQL

Trabajo práctico de la cátedra **Programación III (Tecnicatura Universitaria en Programación - UTN)**.  
Implementa una API REST asincrónica, contratos con DTOs, ejecución concurrente no bloqueante y persistencia relacional con SQLModel, SQLAlchemy 2.0 y PostgreSQL.

---

## 1. Requisitos Técnicos y Dependencias

- **Python**: 3.12+ (probado en Python 3.13)
- **FastAPI**: >= 0.111
- **SQLModel**: >= 0.0.24
- **SQLAlchemy**: >= 2.0 (asincrónico)
- **asyncpg**: >= 0.30 (driver asincrónico para PostgreSQL)
- **python-dotenv**: >= 1.0
- **Uvicorn**: Servidor ASGI
- **PostgreSQL**: 16+

---

## 2. Pasos para Levantar el Proyecto desde Cero

### Paso 1: Clonar el repositorio y acceder a la carpeta
```bash
git clone <url-del-repositorio>
cd TP-Programacion-Veterinaria
```

### Paso 2: Crear y activar el entorno virtual
En Windows (PowerShell):
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```
En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 3: Instalar las dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Configurar variables de entorno (`.env`)
Crear el archivo `.env` a partir de `.env.example`:
```bash
copy .env.example .env     # En Windows
# cp .env.example .env     # En Linux/macOS
```

Asegurarse de que `DATABASE_URL` apunte a la instancia local de PostgreSQL:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/veterinaria_db
ECHO_SQL=True
```

### Paso 5: Inicializar y poblar la base de datos (`reiniciar.py`)
Ejecutar el script provisto para eliminar tablas preexistentes, recrear el esquema relacional con todas sus restricciones e índices, y cargar los datos semilla mínimos requeridos:
```bash
python reiniciar.py
```

### Paso 6: Iniciar el servidor de desarrollo
```bash
uvicorn app.main:app --reload
```
La aplicación quedará disponible en:
- API Base: `http://localhost:8000`
- Documentación interactiva Swagger UI: `http://localhost:8000/docs`
- Documentación alternativa ReDoc: `http://localhost:8000/redoc`
- Verificación de vida (Liveness): `http://localhost:8000/health/live`
- Verificación de base de datos (Readiness): `http://localhost:8000/health/ready`

---

## 3. Justificación Teórica: Índices en Claves Foráneas

### Pregunta de Cátedra:
> **¿Por qué la clave foránea `turno_practica.turno_id` no necesita un índice secundario explícito en PostgreSQL?**

### Explicación Técnica y Justificación:
1. **Comportamiento por defecto de PostgreSQL**: PostgreSQL no crea índices automáticos para las columnas que son claves foráneas (`FOREIGN KEY`). Sin embargo, sí crea automáticamente un índice único de tipo **B-tree** para la **clave primaria** de toda tabla.
2. **Estructura de la clave primaria compuesta**: La tabla intermedia `turno_practica` define una clave primaria compuesta sobre las columnas:
   ```sql
   PRIMARY KEY (turno_id, practica_id)
   ```
   Esto genera en el catálogo del motor un índice B-tree único indexando el par ordenado `(turno_id, practica_id)`.
3. **Propiedad de prefijo izquierdo en índices B-tree**: En un árbol B-tree compuesto por varias columnas `(A, B)`, el motor puede utilizar dicho índice para cualquier consulta, join o comprobación referencial que filtre por la columna líder (el prefijo más a la izquierda, en este caso `turno_id`).  
   Por consiguiente, cuando PostgreSQL valida integridad referencial o ejecuta borrados en cascada por `turno_id` (ej. `DELETE FROM turno_practica WHERE turno_id = ?`), el motor utiliza directamente y con costo logarítmico `O(log N)` el índice de la clave primaria ya existente. Crear un índice secundario sobre `turno_id` resultaría redundante, consumiendo espacio en disco y tiempo de I/O en cada inserción sin beneficio operativo.
4. **Contraste con `practica_id`**: La columna `practica_id` ocupa la segunda posición en el índice compuesto. Un índice sobre `(turno_id, practica_id)` no puede ser recorrido eficazmente buscando solo por `practica_id` sin tener el `turno_id`. Por tal motivo, **`practica_id` sí requiere un índice explícito**, el cual fue declarado en el modelo (`index=True`).

---

## 4. Evidencia del Caso C-07: Consultas Fijas sin Problema N+1

El detalle de un turno (`GET /turnos/{id}`) resuelve la mascota y todas sus prácticas asociadas mediante carga anticipada explícita en SQLAlchemy:
- `joinedload(Turno.mascota)` para la relación "a uno".
- `selectinload(Turno.practicas).joinedload(TurnoPractica.practica)` para la colección de prácticas y sus datos de catálogo.

Con `ECHO_SQL=True` en `.env`, se demuestra en la consola del servidor que **tanto para un turno con 1 práctica como para un turno con 3 prácticas, se emite exactamente la misma cantidad fija de 2 sentencias SQL**:

### Fragmento de Consola (Turno con 1 práctica - ID 3):
```text
INFO:sqlalchemy.engine.Engine:BEGIN (implicit)
INFO:sqlalchemy.engine.Engine:SELECT turno.id AS turno_id, turno.mascota_id AS turno_mascota_id, turno.fecha AS turno_fecha, turno.motivo AS turno_motivo, turno.total AS turno_total, mascota_1.id AS mascota_1_id, mascota_1.nombre AS mascota_1_nombre, mascota_1.especie AS mascota_1_especie, mascota_1.duenio_id AS mascota_1_duenio_id 
FROM turno LEFT OUTER JOIN mascota AS mascota_1 ON mascota_1.id = turno.mascota_id 
WHERE turno.id = $1::INTEGER
INFO:sqlalchemy.engine.Engine:[generated in 0.00030s] (3,)
INFO:sqlalchemy.engine.Engine:SELECT turno_practica.turno_id AS turno_practica_turno_id, turno_practica.practica_id AS turno_practica_practica_id, turno_practica.precio_unitario AS turno_practica_precio_unitario, practica_1.id AS practica_1_id, practica_1.nombre AS practica_1_nombre, practica_1.precio AS practica_1_precio 
FROM turno_practica LEFT OUTER JOIN practica AS practica_1 ON practica_1.id = turno_practica.practica_id 
WHERE turno_practica.turno_id IN ($1::INTEGER)
INFO:sqlalchemy.engine.Engine:[generated in 0.00034s] (3,)
```

### Fragmento de Consola (Turno con 3 prácticas - ID 4):
```text
INFO:sqlalchemy.engine.Engine:BEGIN (implicit)
INFO:sqlalchemy.engine.Engine:SELECT turno.id AS turno_id, turno.mascota_id AS turno_mascota_id, turno.fecha AS turno_fecha, turno.motivo AS turno_motivo, turno.total AS turno_total, mascota_1.id AS mascota_1_id, mascota_1.nombre AS mascota_1_nombre, mascota_1.especie AS mascota_1_especie, mascota_1.duenio_id AS mascota_1_duenio_id 
FROM turno LEFT OUTER JOIN mascota AS mascota_1 ON mascota_1.id = turno.mascota_id 
WHERE turno.id = $1::INTEGER
INFO:sqlalchemy.engine.Engine:[cached since 0.00201s ago] (4,)
INFO:sqlalchemy.engine.Engine:SELECT turno_practica.turno_id AS turno_practica_turno_id, turno_practica.practica_id AS turno_practica_practica_id, turno_practica.precio_unitario AS turno_practica_precio_unitario, practica_1.id AS practica_1_id, practica_1.nombre AS practica_1_nombre, practica_1.precio AS practica_1_precio 
FROM turno_practica LEFT OUTER JOIN practica AS practica_1 ON practica_1.id = turno_practica.practica_id 
WHERE turno_practica.turno_id IN ($1::INTEGER)
INFO:sqlalchemy.engine.Engine:[cached since 0.00205s ago] (4,)
```

**Conclusión**: El número de consultas es exactamente **2**, independientemente del número de prácticas vinculadas al turno, evitando el problema N+1 y erradicando excepciones de carga perezosa (`MissingGreenlet`).

---

## 5. Ejecución de Pruebas

### Pruebas HTTP (REST Client / VS Code / Cursor)
Abrir el archivo [`test/pruebas.http`](test/pruebas.http) y ejecutar las peticiones secuenciales correspondientes a los casos de prueba C-01 a C-09.

### Pruebas Automatizadas con Pytest
```bash
pytest test/test_api.py -v
```

---

## 6. Estructura Modular del Proyecto

```text
TP-Programacion-Veterinaria/
├── app/
│   ├── main.py                     # Lifespan, registro de routers y app state
│   ├── core/
│   │   ├── config.py               # Configuración y lectura de .env
│   │   └── database.py             # Engine asíncrono, fábrica de sesiones y get_session
│   └── modules/
│       ├── health/
│       │   └── router.py           # GET /health/live y GET /health/ready
│       ├── duenios/
│       │   ├── models.py           # Modelos Duenio y FichaDuenio (1 a 1)
│       │   ├── schemas.py          # DTOs Create, Update, Read
│       │   ├── service.py          # Lógica, captura IntegrityError, joinedload
│       │   └── router.py           # Rutas CRUD de dueños y fichas
│       ├── mascotas/
│       │   ├── models.py           # Modelo Mascota (FK duenio_id RESTRICT)
│       │   ├── schemas.py          # DTOs y envoltorio de paginación
│       │   ├── service.py          # Lógica de paginación con validación 422
│       │   └── router.py           # Rutas /mascotas/
│       ├── practicas/
│       │   ├── models.py           # Modelo Practica (CHECK precio > 0, UNIQUE)
│       │   ├── schemas.py          # DTOs con validación gt=0
│       │   ├── service.py          # Catálogo de prácticas
│       │   └── router.py           # Rutas /practicas/
│       ├── turnos/
│       │   ├── models.py           # Modelos Turno y TurnoPractica (PK compuesta)
│       │   ├── schemas.py          # DTOs de turno y prácticas congeladas
│       │   ├── service.py          # Alta atómica, congelamiento de precio, cascada
│       │   └── router.py           # Rutas /turnos/
│       └── laboratorio/
│           ├── cliente.py          # Código bloqueante sincrónico provisto por la cátedra
│           ├── service.py          # Delegación fuera del event loop con asyncio.to_thread
│           └── router.py           # GET /laboratorio/stock/{vacuna}
├── test/
│   ├── pruebas.http                # Casos de prueba C-01 a C-09 documentados
│   ├── c08_check_test.sql          # Sentencia SQL para probar el rechazo por CHECK
│   └── test_api.py                 # Suite de pruebas automatizadas con pytest y httpx
├── knowledge-base/                 # Base de conocimiento canónica (10 documentos canónicos)
├── CHANGES.md                      # Roadmap canónico de implementación
├── AGENTS.md                       # Reglas duras y arquitectura para agentes
├── reiniciar.py                    # Script de reinicio y siembra de base de datos
├── requirements.txt                # Dependencias con versiones
├── .env.example                    # Plantilla de variables de entorno
├── .gitignore                      # Exclusión de credenciales y temporales
└── README.md                       # Documentación principal del trabajo práctico
```
