# Funcionalidades

Organizadas por épicas e historias de usuario (US-NNN) con criterios de aceptación explícitos alineados a las consignas del TP.

---

## Épica 1: Monitoreo y Ciclo de Vida

### US-001 — Health Live y Ready
**Como** sistema de monitoreo / orquestador  
**Quiero** consultar los endpoints `/health/live` y `/health/ready`  
**Para** saber si el contenedor/proceso está vivo y si la conexión a la base de datos está lista.

**Criterios de Aceptación**:
- [ ] `GET /health/live` responde HTTP 200 con `{"estado": "vivo"}` sin realizar consultas a la base de datos.
- [ ] `GET /health/ready` ejecuta `SELECT 1` a través de la sesión asincrónica. Si la conexión responde, retorna HTTP 200 con `{"estado": "base de datos conectada"}`.
- [ ] Si la base de datos no está disponible o rechaza la conexión, `GET /health/ready` responde HTTP 503 con `{"estado": "base de datos no disponible"}`.

---

## Épica 2: Gestión de Dueños y Fichas

### US-002 — Alta de Dueño
**Como** operador de la veterinaria  
**Quiero** dar de alta a un dueño con su nombre y email  
**Para** registrar clientes en el sistema.

**Criterios de Aceptación**:
- [ ] `POST /duenios/` recibe `DuenioCreate` (`nombre`, `email`).
- [ ] Retorna HTTP 201 con `DuenioRead` (`id`, `nombre`, `email`, `ficha=None`).
- [ ] Si el email ya está registrado, retorna HTTP 409 capturando `IntegrityError`.
- [ ] Validación de email y campos obligatorios retorna HTTP 422 si el body es inválido.

### US-003 — Consulta de Dueño con su Ficha
**Como** operador de la veterinaria  
**Quiero** obtener los datos de un dueño por su ID  
**Para** ver su información de contacto y ficha.

**Criterios de Aceptación**:
- [ ] `GET /duenios/{id}` retorna HTTP 200 con el objeto dueño y su `ficha` resuelta como objeto (o `null` si no tiene).
- [ ] Utiliza carga anticipada `joinedload(Duenio.ficha)` para resolver la relación en una sola consulta.
- [ ] Si el `{id}` no es entero (ej. `/duenios/abc`), FastAPI responde HTTP 422 antes de invocar el handler.
- [ ] Si el dueño no existe, responde HTTP 404.

### US-004 — Actualización Parcial de Dueño (PATCH)
**Como** operador de la veterinaria  
**Quiero** modificar únicamente el nombre o el email de un dueño  
**Para** actualizar sus datos sin necesidad de reenviar toda la entidad.

**Criterios de Aceptación**:
- [ ] `PATCH /duenios/{id}` recibe `DuenioUpdate` con campos opcionales.
- [ ] Aplica únicamente los campos efectivamente enviados usando `.model_dump(exclude_unset=True)`.
- [ ] Si el nuevo email ya pertenece a otro dueño, captura `IntegrityError` y responde HTTP 409.
- [ ] Si el dueño no existe, responde HTTP 404.

### US-005 — Eliminación de Dueño con Restricción
**Como** operador de la veterinaria  
**Quiero** eliminar un dueño que ya no sea cliente  
**Para** mantener limpia la base de datos.

**Criterios de Aceptación**:
- [ ] Si el dueño tiene mascotas asociadas, la base rechaza el borrado (`ON DELETE RESTRICT`) y el service responde HTTP 409.
- [ ] Si el dueño no tiene mascotas, se elimina exitosamente y responde HTTP 204 (sin cuerpo).
- [ ] Si el dueño no existe, responde HTTP 404.

### US-006 — Registro de Ficha de Dueño
**Como** operador de la veterinaria  
**Quiero** registrar la ficha de contacto (`telefono`, `direccion`) de un dueño  
**Para** tener sus datos de contacto actualizados.

**Criterios de Aceptación**:
- [ ] `POST /duenios/{id}/ficha` recibe `FichaCreate` (`telefono`, `direccion`).
- [ ] Si el dueño no existe, responde HTTP 404.
- [ ] Si el dueño ya posee una ficha, la restricción `UNIQUE (duenio_id)` rechaza la inserción y el service responde HTTP 409.
- [ ] En caso de éxito, retorna HTTP 201 con `FichaRead`.

---

## Épica 3: Gestión de Mascotas y Paginación

### US-007 — Alta de Mascota
**Como** operador de la veterinaria  
**Quiero** registrar una mascota asignándola a su dueño  
**Para** vincularla en el sistema.

**Criterios de Aceptación**:
- [ ] `POST /mascotas/` recibe `MascotaCreate` (`nombre`, `especie`, `duenio_id`).
- [ ] Si el `duenio_id` no existe en la base, PostgreSQL rechaza por FK y el service responde HTTP 409.
- [ ] En caso de éxito, responde HTTP 201 con `MascotaRead`.

### US-008 — Listado Paginado de Mascotas
**Como** operador de la veterinaria  
**Quiero** consultar la lista de mascotas paginada con parámetros `page` y `size`  
**Para** navegar ordenadamente por el padrón de mascotas.

**Criterios de Aceptación**:
- [ ] Parámetros de consulta: `page` (default 1, `>= 1`), `size` (default 20, rango 1 a 100).
- [ ] Respuesta con estructura `{ items, total, page, size, pages }`.
- [ ] `pages = ceil(total / size)` (o 1 si total es 0).
- [ ] Si `page > pages` y la base tiene registros (`total > 0`), responde HTTP 422.
- [ ] La primera página (`page=1`) siempre responde con éxito HTTP 200, incluso si `total == 0` (`items: []`).

### US-009 — Consulta de Mascota con Dueño
**Como** operador de la veterinaria  
**Quiero** obtener los detalles de una mascota y su dueño  
**Para** identificar quién es el responsable de la atención.

**Criterios de Aceptación**:
- [ ] `GET /mascotas/{id}` retorna HTTP 200 con los datos de la mascota y el objeto `duenio` anidado.
- [ ] Emplea `joinedload(Mascota.duenio)` para evitar N+1.
- [ ] Si no existe, retorna HTTP 404.

---

## Épica 4: Catálogo de Prácticas Médicas

### US-010 — Alta y Consulta del Catálogo de Prácticas
**Como** administrador o veterinario  
**Quiero** registrar prácticas con su precio vigente y consultar el catálogo completo  
**Para** tarifar los servicios de la veterinaria.

**Criterios de Aceptación**:
- [ ] `POST /practicas/` recibe `PracticaCreate` (`nombre`, `precio: Decimal > 0`).
- [ ] Si el nombre ya existe, responde HTTP 409 por constraint UNIQUE.
- [ ] Si el precio es `<= 0`, responde HTTP 422 por validación Pydantic y falla por CHECK en base si se evade la API.
- [ ] `GET /practicas/` lista todas las prácticas vigentes con HTTP 200.

---

## Épica 5: Reserva y Cancelación de Turnos

### US-011 — Alta Atómica de Turno con Prácticas Congeladas
**Como** operador de la veterinaria  
**Quiero** agendar un turno para una mascota indicando las prácticas que se realizarán  
**Para** reservar la consulta y fijar los costos de atención.

**Criterios de Aceptación**:
- [ ] `POST /turnos/` recibe `TurnoCreate` (`mascota_id`, `fecha`, `motivo`, `practicas: [{practica_id: ...}]`).
- [ ] No viajan precios ni total en el cuerpo de la petición.
- [ ] Si la lista `practicas` está vacía, responde HTTP 422 (`RN-05`).
- [ ] Si la mascota o alguna práctica no existen en la base, responde HTTP 409/404 y **no se persiste nada** en la base (transacción atómica).
- [ ] Si una práctica viene repetida en la lista, la clave primaria compuesta `(turno_id, practica_id)` rechaza la inserción y responde HTTP 409 (`RN-07`).
- [ ] El service consulta los precios vigentes, los congela en cada fila de `turno_practica.precio_unitario`, calcula el `total = sum(precios)` y persiste turno y prácticas en una única transacción.
- [ ] Retorna HTTP 201 con `TurnoRead` detallando mascota, lista de prácticas con su nombre y `precio_unitario`, y `total` calculado.

### US-012 — Detalle de Turno y Borrado en Cascada
**Como** operador de la veterinaria  
**Quiero** ver el detalle de un turno agendado o cancelarlo/eliminarlo  
**Para** gestionar la agenda de la clínica.

**Criterios de Aceptación**:
- [ ] `GET /turnos/{id}` retorna HTTP 200 con la información del turno, la mascota (`joinedload`) y todas sus prácticas asociadas (`selectinload`).
- [ ] La consulta se resuelve con un número constante y fijo de queries independientemente de la cantidad de prácticas (sin N+1).
- [ ] `DELETE /turnos/{id}` elimina el turno y sus prácticas asociadas automáticamente por `ON DELETE CASCADE` en PostgreSQL (`passive_deletes=True` en ORM). Retorna HTTP 204 sin cuerpo.

---

## Épica 6: Integración con Laboratorio

### US-013 — Consulta No Bloqueante de Stock de Vacunas
**Como** veterinario  
**Quiero** verificar el stock de vacunas con el laboratorio  
**Para** saber si hay disponibilidad sin demorar ni congelar el servidor web.

**Criterios de Aceptación**:
- [ ] `GET /laboratorio/stock/{vacuna}` ejecuta la función sincrónica bloqueante provista `cliente.consultar_stock(vacuna)` sin modificar su código.
- [ ] Se ejecuta fuera del event loop principal usando `asyncio.to_thread` o `fastapi.concurrency.run_in_threadpool`.
- [ ] Peticiones simultáneas a `/laboratorio/stock/{vacuna}` no demoran las respuestas inmediatas de `GET /health/live`.
