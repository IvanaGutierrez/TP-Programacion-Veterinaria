# Preguntas Abiertas e Inconsistencias

## Inconsistencias Detectadas y Resoluciones

### IN-01 — Formato de serialización de montos monetarios en respuestas JSON
- **Dilema**: En Python se manejan como `Decimal`. Al serializar a JSON, ¿deben devolverse como cadenas de texto (ej. `"27000.00"`) o números?
- **Resolución**: Siguiendo el ejemplo explícito de la consigna (Página 8):
  ```json
  "total": "27000.00",
  "practicas": [
    { "practica_id": 1, "nombre": "Consulta", "precio_unitario": "15000.00" }
  ]
  ```
  Se serializan como cadenas formateadas a dos decimales para evitar que los clientes JavaScript conviertan los números a `float` de 64 bits y pierdan precisión.

### IN-02 — Caso borde en paginación: Base de datos vacía
- **Dilema**: Si la tabla de mascotas no tiene registros (`total = 0`), ¿qué responde `GET /mascotas/?page=1&size=20`?
- **Resolución**: La consigna establece: *"Una página más allá de pages responde 422; la primera página siempre responde, aunque no haya resultados"*. Por lo tanto, si `total == 0`, `pages` es `1` (o la condición `page == 1` tiene excepción explícita) y responde HTTP 200 con `{ items: [], total: 0, page: 1, size: 20, pages: 1 }`.

## Preguntas Abiertas (Priorizadas)
| Prioridad | Pregunta | Bloquea | Decisor | Estado |
|---|---|---|---|---|
| Baja | ¿Se requiere soporte para Docker / docker-compose en la entrega? | Opcional | Cátedra / Alumno | Resuelto: se provee script `reiniciar.py` y opcionalmente puede añadirse compose si se requiere. |
| Baja | ¿Es necesario contemplar endpoints de actualización para prácticas o turnos? | Fuera de alcance | Cátedra | Resuelto: la consigna solo pide CRUD parcial específico (POST/GET/PATCH/DELETE para dueño, POST/GET para mascotas y prácticas, POST/GET/DELETE para turnos). |
