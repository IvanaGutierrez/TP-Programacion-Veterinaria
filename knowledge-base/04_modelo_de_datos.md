# Modelo de Datos

## Dominios y Tipos de Relaciones
El modelo traduce los tipos de relaciones fundamentales del Capítulo 4:
1. **Uno a uno**: `duenio` y `ficha_duenio`. Clave foránea en `ficha_duenio.duenio_id` con restricción de unicidad (`UNIQUE`). En `Duenio`, la ficha se resuelve como objeto individual (`Optional[FichaDuenioRead]`), no como lista.
2. **Agregación**: `duenio` y `mascota`. La mascota existe independientemente pero referencia a su dueño. Regla de borrado `ON DELETE RESTRICT`: mientras un dueño tenga mascotas a su nombre, no puede eliminarse.
3. **Asociación**: `turno` y `mascota`. El turno conoce a la mascota atendida (`mascota_id`), pero ninguno es dueño del ciclo de vida del otro.
4. **Composición y Muchos a Muchos con datos propios**: `turno`, `practica` y `turno_practica`. Una práctica reservada (`TurnoPractica`) no tiene sentido sin su turno: nace con él y se borra con él (`ON DELETE CASCADE` en la base y `passive_deletes=True` en el ORM). Almacena el `precio_unitario` congelado en el momento de la reserva.

## ERD (Diagrama Entidad-Relación)
```text
+---------------------+              +-----------------------+
|       duenio        | 1          1 |      ficha_duenio     |
+---------------------+--------------+-----------------------+
| PK id (int)         |              | PK id (int)           |
|    nombre (str)     |              | FK duenio_id (UNIQUE) |
|    email (str UNIQUE)              |    telefono (str)     |
+----------+----------+              |    direccion (str)    |
           | 1                       +-----------------------+
           |
           | 0..N
+----------v----------+
|       mascota       | 1
+---------------------+
| PK id (int)         |
|    nombre (str)     |
|    especie (str)    |
| FK duenio_id (idx)  |
+----------+----------+
           |
           | 0..N
+----------v----------+              +-----------------------+
|        turno        | 1          N |       practica        |
+---------------------+              +-----------------------+
| PK id (int)         |              | PK id (int)           |
| FK mascota_id (idx) |              |    nombre (str UNIQUE)|
|    fecha (timestamptz)             |    precio (NUMERIC)   |
|    motivo (str)     |              +-----------+-----------+
|    total (NUMERIC)  |                          | 1
+----------+----------+                          |
           | 1                                   |
           | (ON DELETE CASCADE)                 | 0..N
+----------v-------------------------------------v-----------+
|                       turno_practica                       |
+------------------------------------------------------------+
| PK, FK turno_id (int)                                      |
| PK, FK practica_id (int, idx)                              |
|        precio_unitario (NUMERIC 10,2 > 0)                  |
+------------------------------------------------------------+
```

## Entidades y Diccionario de Datos

### 1. `duenio`
- `id`: `int | None = Field(default=None, primary_key=True)`
- `nombre`: `str = Field(nullable=False)`
- `email`: `str = Field(nullable=False, unique=True, index=True)`
- **Relaciones**:
  - `ficha`: `Optional["FichaDuenio"] = Relationship(back_populates="duenio", cascade_delete=True)`
  - `mascotas`: `list["Mascota"] = Relationship(back_populates="duenio")`

### 2. `ficha_duenio`
- `id`: `int | None = Field(default=None, primary_key=True)`
- `duenio_id`: `int = Field(foreign_key="duenio.id", unique=True, nullable=False, ondelete="CASCADE")`
- `telefono`: `str = Field(nullable=False)`
- `direccion`: `str = Field(nullable=False)`
- **Relaciones**:
  - `duenio`: `Optional["Duenio"] = Relationship(back_populates="ficha")`

### 3. `mascota`
- `id`: `int | None = Field(default=None, primary_key=True)`
- `nombre`: `str = Field(nullable=False)`
- `especie`: `str = Field(nullable=False)`
- `duenio_id`: `int = Field(foreign_key="duenio.id", nullable=False, ondelete="RESTRICT", index=True)`
- **Relaciones**:
  - `duenio`: `Optional["Duenio"] = Relationship(back_populates="mascotas")`
  - `turnos`: `list["Turno"] = Relationship(back_populates="mascota")`

### 4. `practica`
- `id`: `int | None = Field(default=None, primary_key=True)`
- `nombre`: `str = Field(nullable=False, unique=True, index=True)`
- `precio`: `Decimal = Field(sa_column=Column(Numeric(10, 2), CheckConstraint("precio > 0"), nullable=False))`
- **Relaciones**:
  - `turno_practicas`: `list["TurnoPractica"] = Relationship(back_populates="practica")`

### 5. `turno`
- `id`: `int | None = Field(default=None, primary_key=True)`
- `mascota_id`: `int = Field(foreign_key="mascota.id", nullable=False, index=True)`
- `fecha`: `datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))`
- `motivo`: `str = Field(nullable=False)`
- `total`: `Decimal = Field(sa_column=Column(Numeric(12, 2), CheckConstraint("total >= 0"), nullable=False))`
- **Relaciones**:
  - `mascota`: `Optional["Mascota"] = Relationship(back_populates="turnos")`
  - `turno_practicas`: `list["TurnoPractica"] = Relationship(back_populates="turno", cascade_delete=True, passive_deletes=True)`

### 6. `turno_practica`
- `turno_id`: `int = Field(foreign_key="turno.id", primary_key=True, ondelete="CASCADE")`
- `practica_id`: `int = Field(foreign_key="practica.id", primary_key=True, index=True)`
- `precio_unitario`: `Decimal = Field(sa_column=Column(Numeric(10, 2), CheckConstraint("precio_unitario > 0"), nullable=False))`
- **Relaciones**:
  - `turno`: `Optional["Turno"] = Relationship(back_populates="turno_practicas")`
  - `practica`: `Optional["Practica"] = Relationship(back_populates="turno_practicas")`

## Índices de Claves Foráneas
PostgreSQL **no crea índices automáticos** para las columnas que son claves foráneas. Por ende:
- Se agregan índices explícitos en `mascota.duenio_id`, `turno.mascota_id` y `turno_practica.practica_id`.
- **Excepción justificada**: `turno_practica.turno_id` **no necesita** un índice secundario explícito. Al ser la primera columna de la clave primaria compuesta `(turno_id, practica_id)`, PostgreSQL genera automáticamente un índice B-tree único sobre dicho par. En árboles B-tree, cualquier búsqueda o join que filtre por el prefijo izquierdo (en este caso `turno_id`) utiliza de forma óptima el índice de la clave primaria.

## Seed data inicial (`reiniciar.py`)
Mínimo obligatorio requerido por la consigna:
- **Dueños (2)**:
  1. Juan Pérez (`juan.perez@example.com`) con Ficha (`11-4455-6677`, `Av. Corrientes 1234`).
  2. María Gómez (`maria.gomez@example.com`) sin ficha inicial.
- **Mascotas (3)**:
  1. "Toby" (perro) -> Dueño 1 (Juan Pérez).
  2. "Milo" (gato) -> Dueño 1 (Juan Pérez).
  3. "Luna" (perro) -> Dueño 2 (María Gómez).
- **Prácticas (4)**:
  1. "Consulta general", $15000.00
  2. "Vacuna séxtuple", $18000.00
  3. "Vacuna antirrábica", $12000.00
  4. "Desparasitación", $8000.00
- **Turno (1 con 2 prácticas)**:
  - Turno 1 para Mascota 1 ("Toby"), fecha en zona horaria, motivo "Control y vacunación", con prácticas 1 ("Consulta general", $15000.00) y 3 ("Vacuna antirrábica", $12000.00). Total calculado: $27000.00.
