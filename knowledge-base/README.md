# Base de Conocimiento — Veterinaria API (UTN Programación III)

Base de conocimiento estructurada y canónica para el Trabajo Práctico "Veterinaria — FastAPI y PostgreSQL" de la cátedra Programación III (UTN).

## Índice Canónico de Archivos

| Archivo | Contenido |
|---|---|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito del sistema, objetivos por actor, alcance v1.0 y exclusiones. |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack tecnológico completo, arquitectura general y tabla de endpoints. |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores del sistema y aclaración de ausencia de autenticación (fuera de alcance). |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Entidades SQLModel, ERD, restricciones (PK, FK, UNIQUE, CHECK), índices y seed data. |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | Reglas RN-01 a RN-09 y principios de concurrencia e integridad en PostgreSQL. |
| [06_funcionalidades.md](06_funcionalidades.md) | Historias de usuario por épica con criterios de aceptación detallados. |
| [07_flujos_principales.md](07_flujos_principales.md) | Flujos atómicos de alta de turnos, borrado cascada vs restrict, y concurrencia asincrónica. |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Estructura modular de carpetas, lifespan, inyección de dependencias y variables de entorno. |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | Decisiones de arquitectura (DD-01 a DD-07) justificadas técnicamente y supuestos. |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias resueltas y preguntas abiertas de baja prioridad. |

## Resumen Ejecutivo
El proyecto implementa una API REST asincrónica con FastAPI, SQLModel y PostgreSQL para una veterinaria de barrio. Resuelve íntegramente los cuatro capítulos de la materia:
1. Ciclo de vida y gestión de recursos con `lifespan` y dependencias `Depends(get_session)`.
2. Contratos DTO estrictos separados de modelos de base de datos, códigos HTTP semánticos y paginación controlada.
3. Asincronía real y no bloqueante delegando código sincrónico fuera del bucle de eventos.
4. Persistencia relacional avanzada: 1 a 1 (`duenio` - `ficha_duenio`), 1 a N (`duenio` - `mascota`), N a M con atributos propios (`turno` - `practica` a través de `turno_practica`), carga anticipada (`joinedload` y `selectinload`) para evitar el problema N+1 y `MissingGreenlet`, y garantías delegadas en la base (`UNIQUE`, `CHECK`, `RESTRICT` y `CASCADE`).
