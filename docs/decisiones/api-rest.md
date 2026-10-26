# Decisiones de diseño - API REST de consulta (Guía 4)

**Proyecto:** FinaGotchi · **Rama:** `feature/api-rest-consultas`

## Contrato de consulta del equipo (Actividad 1)

| Pregunta | Respuesta del equipo |
|---|---|
| ¿Qué recursos expondrá la API? | `devices` (dispositivos detectados) y `measurements` (transacciones de voz registradas por el simulador). |
| ¿Qué endpoint devuelve todos los dispositivos? | `GET /api/devices` |
| ¿Qué endpoint devuelve un dispositivo específico? | `GET /api/devices/{device_id}` |
| ¿Cómo se filtrarán mediciones por device_id? | Query parameter: `GET /api/measurements?device_id=FINAGOTCHI-PC-SIMULATOR-01` |
| ¿Qué respuesta se espera si el dispositivo no existe? | `404 Not Found` en `/api/devices/{device_id}`; en `/api/measurements?device_id=...` un `200` con lista vacía `[]`. |
| ¿Qué límite máximo de registros permitirá la API? | `limit` entre 1 y 100 (por defecto 20); `offset` >= 0. Fuera de rango responde `422`. |

## Endpoints

| Método | Ruta | Propósito | Códigos |
|---|---|---|---|
| POST | `/api/v1/finagotchi/telemetry` | Recibe la lectura del simulador (ya existente) | 201, 400, 409 |
| GET | `/health` | Estado del servicio | 200 |
| GET | `/api/measurements` | Histórico paginado (más recientes primero) | 200, 422 |
| GET | `/api/devices` | Lista de dispositivos | 200 |
| GET | `/api/devices/{device_id}` | Resumen de un dispositivo | 200, 404 |
| GET | `/docs` · `/openapi.json` | Swagger UI / especificación OpenAPI | 200 |

## Justificación (≈120 palabras)

Usamos nombres de recursos en plural y el método GET, sin verbos en la ruta, para que el contrato sea predecible. Los dispositivos se obtienen agrupando `transacciones` por `device_id`, así que no hace falta una tabla nueva. Cada medición devuelve `measurements` como objeto JSON (texto de voz, tipo, monto y categoría) para que el cliente no tenga que interpretar columnas de la base de datos. El `limit` máximo de 100 protege al servidor de respuestas enormes; es una decisión académica. Una consulta válida sin resultados devuelve `200` con `[]` porque no es un error; un dispositivo inexistente devuelve `404` porque el recurso solicitado no existe. El futuro dashboard consumirá esta API y no abrirá `finagotchi.db`.

## Notas de adaptación

- El backend del proyecto usa **Flask** (no FastAPI), por eso `limit`/`offset` se validan a mano y Swagger se sirve con Swagger UI sobre `/openapi.json`.
- La tabla se llama `transacciones` y la ruta POST es `/api/v1/finagotchi/telemetry`; los GET mantienen los nombres que pide la guía.
- Se agregaron las columnas `sequence` y `received_at` (migración automática en `database/init_db.py`). Las filas anteriores a la migración tienen esos campos en `null`.
- Zona horaria: todos los timestamps están en UTC.
- Puerto `8000` (en macOS el `5000` lo ocupa AirPlay Receiver).
