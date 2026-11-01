# Actores y Roles

## Actores del sistema
| Actor | Descripción | Cómo interactúa |
|---|---|---|
| Operador de Veterinaria / Recepcionista | Registra clientes, fichas de contacto y mascotas. Administra turnos de atención y revisa stock de vacunas. | Mediante clientes HTTP / frontend consumiendo la API REST. |
| Sistema de Monitoreo / Orquestador | Consulta el estado operativo del servicio y la conectividad con la base de datos PostgreSQL. | Mediante endpoints `/health/live` y `/health/ready`. |
| Administrador de Base de Datos / Alumno | Ejecuta el script de recreación y siembra (`reiniciar.py`) y verifica los casos de prueba con `test/pruebas.http`. | Mediante consola de terminal y extensiones REST client. |

## RBAC — Matriz de permisos
> **Nota de alcance**: Siguiendo las directivas de la cátedra para el TP (Unidades 1 a 4), la autenticación y autorización están **explícitamente fuera de alcance**. No se implementa RBAC, tokens JWT ni verificación de credenciales en los endpoints de la API.

| Rol | Recurso | Permisos |
|---|---|---|
| Público / Libre | Todos los endpoints de la API | CRUD completo sin restricciones de autenticación |

## Rutas públicas
Todas las rutas del sistema son públicas y no requieren headers de autorización:
- `/health/live`, `/health/ready`
- `/duenios/` y subrutas (`/{id}`, `/{id}/ficha`, `/{id}/mascotas`)
- `/mascotas/` y subrutas (`/{id}`)
- `/practicas/`
- `/turnos/` y subrutas (`/{id}`)
- `/laboratorio/stock/{vacuna}`
- `/docs`, `/redoc`, `/openapi.json` (documentación Swagger / OpenAPI de FastAPI)
