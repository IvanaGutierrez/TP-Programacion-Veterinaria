# Decisiones y Supuestos

## Decisiones Documentadas (Architecture Decision Records)

### DD-01 — Uso estricto de `Decimal` para representación monetaria
- **Decisión**: Todos los campos monetarios (`practica.precio`, `turno.total`, `turno_practica.precio_unitario`) se modelan con `Decimal` de Python y tipo `Numeric(10,2)` o `Numeric(12,2)` en PostgreSQL.
- **Contexto**: Los tipos de coma flotante (`float`) presentan imprecisiones de redondeo binario inaceptables en transacciones comerciales y contables (Sección 2.7).
- **Alternativas consideradas**: `float` (descartado por pérdida de precisión), `int` en centavos (descartado por requisito de cátedra).
- **Justificación**: Cumple estrictamente con la consigna y garantiza exactitud centesimal.

### DD-02 — Configuración `expire_on_commit=False` en la fábrica de sesiones
- **Decisión**: Configurar `expire_on_commit=False` en el `async_sessionmaker`.
- **Contexto**: Por defecto, SQLAlchemy expira los atributos de las entidades tras un `commit()`. En un entorno asincrónico, cualquier intento de acceder a un atributo post-commit desencadena una carga diferida implícita (lazy load) que arroja `sqlalchemy.exc.MissingGreenlet` (Sección 4.5).
- **Justificación**: Mantiene los objetos en memoria utilizables tras el commit para serializar las respuestas DTO sin fallas ni consultas adicionales.

### DD-03 — `passive_deletes=True` en la relación `Turno.turno_practicas`
- **Decisión**: Configurar `passive_deletes=True` en `Relationship(back_populates="turno", cascade_delete=True, passive_deletes=True)`.
- **Contexto**: La clave foránea en la base de datos ya declara `ON DELETE CASCADE`. Sin `passive_deletes=True`, SQLAlchemy intenta cargar las filas hijas o emitir sentencias `UPDATE ... SET turno_id = NULL` o `DELETE` individuales.
- **Justificación**: Delega el borrado en cascada completamente al motor PostgreSQL, optimizando la performance y evitando emisiones redundantes de SQL.

### DD-04 — Justificación del índice compuesto en `turno_practica`
- **Decisión**: No declarar índice secundario sobre `turno_practica.turno_id`. Sí declarar índice explícito en `turno_practica.practica_id`.
- **Contexto**: PostgreSQL no crea índices automáticos para claves foráneas.
- **Justificación**: La clave primaria de la tabla intermedia es compuesta: `PRIMARY KEY (turno_id, practica_id)`. PostgreSQL crea automáticamente un índice B-tree único sobre dicho par. En árboles B-tree, cualquier búsqueda o join por la columna líder (`turno_id`) aprovecha directamente dicho índice. En cambio, para buscar por `practica_id` (segunda columna) se requiere un índice propio.

### DD-05 — Carga anticipada explícita (`joinedload` y `selectinload`)
- **Decisión**: Prohibir totalmente la carga perezosa (lazy loading). Emplear `joinedload` para relaciones "a uno" y `selectinload` para relaciones "a muchos".
- **Contexto**: En SQLAlchemy 2.0 asincrónico, la carga perezosa falla con `MissingGreenlet` y en sistemas sincrónicos provoca el problema N+1.
- **Justificación**: `joinedload` realiza un `LEFT OUTER JOIN` eficiente en la misma consulta para relaciones a uno (`Duenio.ficha`, `Mascota.duenio`, `Turno.mascota`), mientras que `selectinload` realiza una segunda consulta con `IN (...)` para colecciones (`Turno.turno_practicas`), logrando un número fijo de queries independiente de la cantidad de registros.

### DD-06 — Manejo de integridad sin SELECT previo ("Look Before You Leap" antipattern)
- **Decisión**: No realizar `SELECT` previo para chequear duplicados o estados. Insertar/actualizar directamente y capturar `IntegrityError` con rollback y código HTTP 409.
- **Contexto**: Las verificaciones previas sufren de condiciones de carrera (race conditions) entre el SELECT y el INSERT en entornos concurrentes.
- **Justificación**: La base de datos es la única fuente de verdad transaccional. PostgreSQL garantiza atomicidad e integridad; el servicio traduce el error a HTTP 409 con mensaje claro al usuario.

### DD-07 — Aislamiento de llamadas sincrónicas bloqueantes mediante `asyncio.to_thread`
- **Decisión**: Envolver `cliente.consultar_stock(vacuna)` en `await asyncio.to_thread(...)`.
- **Contexto**: La función provista por la cátedra duerme durante 1 segundo mediante `time.sleep(1)`. Si se invoca en el event loop, congela todas las peticiones entrantes.
- **Justificación**: Despacha la ejecución a un pool de hilos de trabajo gestionado por Python, manteniendo libre el bucle de eventos para atender peticiones críticas como `/health/live` con latencia despreciable.

---

## Supuestos Inferidos

### SU-01 — Driver y cadena de conexión PostgreSQL
- **Supuesto**: Se utiliza `postgresql+asyncpg://` como esquema en `DATABASE_URL`.
- **Mitigación**: `app/core/config.py` valida la cadena y `.env.example` proporciona el formato exacto.

### SU-02 — Zona horaria de los turnos
- **Supuesto**: Las fechas de los turnos se almacenan con tipo `DateTime(timezone=True)` en SQLModel / `TIMESTAMP WITH TIME ZONE` en PostgreSQL y se aceptan cadenas ISO 8601 con offset (ej. `-03:00`).
