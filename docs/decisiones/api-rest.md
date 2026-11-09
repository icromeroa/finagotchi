# Decisiones de diseño REST (Guia 4 — capa de compatibilidad)

> FinaGotchi conserva su API v1 (`/api/v1/…`, Flask, `{ok,data}`). Esta capa
> **compat** expone sin prefijo v1 los tres recursos de la Guia 4 y responde
> **JSON plano** de la guia (lista/dict), no el sobre `{ok,data}`.

## Contrato de consulta del equipo (Actividad 1)

| Pregunta | Respuesta del equipo |
|---|---|
| ¿Qué recursos expondrá la API? | `devices` (dispositivos detectados) y `measurements` (transacciones de voz registradas por el simulador). |
| ¿Qué endpoint devuelve todos los dispositivos? | `GET /api/devices` |
| ¿Qué endpoint devuelve un dispositivo específico? | `GET /api/devices/{device_id}` |
| ¿Cómo se filtrarán mediciones por `device_id`? | Query parameter: `GET /api/measurements?device_id=FINAGOTCHI-PC-SIMULATOR-01` |
| ¿Qué respuesta se espera si el dispositivo no existe? | `404 Not Found` en `/api/devices/{device_id}`; en `/api/measurements?device_id=...` un `200` con lista vacía `[]`. |
| ¿Qué límite máximo de registros permitirá la API? | `limit` entre 1 y 100 (por defecto 20); `offset` >= 0. Fuera de rango responde `422`. |

## Recursos

| Recurso | Endpoint |
|---|---|
| Lecturas de telemetría | `POST /api/telemetry` → `GET /api/measurements` |
| Dispositivos conocidos | `GET /api/devices` |
| Un dispositivo | `GET /api/devices/<device_id>` |
| Salud | `GET /health` |
| Docs | `GET /docs` (OpenAPI mínimo con los 5 paths) |

## Mapeo telemetría ↔ dominio FinaGotchi

| Campo Guia 4 | Columna FinaGotchi (`mensajes_dispositivo`) |
|---|---|
| `device_id` | `device_uid` (TEXT libre; idempotencia por `message_id`) |
| `message_id` | `message_id` (UNIQUE por usuario; duplicado devuelve la fila existente con 201) |
| `sequence` | `secuencia` (auto si se omite: MAX+1 por dispositivo) |
| `timestamp` / `received_at` | `recibido_en` (ISO8601 UTC; si falta, `now_utc()`) |
| `measurements` (dict/list) | `texto_transcrito` = `json.dumps(measurements)`; al leer se hace `json.loads` de vuelta a objeto |

No hay cambios de esquema ni migraciones: se reutiliza `mensajes_dispositivo` con `origen='manual'`, `estado='recibido'`.

## Filtros, validación y errores

* `device_id`: igualdad exacta sobre `device_uid`. Sin filtro → todos los del usuario autenticado.
* `limit` (1–100, default 20) y `offset` (≥0, default 0). Fuera de rango o no entero → **422**.
* `from` / `to`: ISO8601 UTC, operan con `>=` y `<=` sobre `recibido_en`. Fechas inválidas → **422**.
* `GET /api/devices/<id>` sin mediciones → **404**.
* `GET /api/measurements` sin coincidencias → **200 + []** (lista vacía, no error artificial).
* Éxito de GET → **200**; POST → **201**.
* Auth: `Authorization: Bearer <access_token>` igual que en `/api/v1` (401/423 si falta/inválido). Respuesta de error en esta capa reutiliza el formato `{ok:false, error:{codigo,mensaje}}` del proyecto.

## Filtros horarios (Fase 5 de la guia)

`from`/`to` se implementan sobre `recibido_en` en UTC. El cliente v1 conserva rangos lógicos (`narc.resolver_rango()`); esta capa solo acepta ISO8601 y aplica comparación lexicográfica sobre el texto normalizado UTC.

## Justificación (150 palabras)

La Guia 4 pide diseño orientado a recursos, paginación y manejo consistente de errores. FinaGotchi ya cumplía eso en `/api/v1/transactions` con diseño propio (`/api/v1/device`, `transactions`, `messages`). En vez de migrar a FastAPI o duplicar la base, se agregó una **capa de compatibilidad Flask** sin esquema nuevo, reutilizando `mensajes_dispositivo` como telemetría. Así, el flujo simulador→POST→SQLite→GET queda demostrable con los endpoints exactos de la guia, la paginación `limit/offset` y los códigos 200/404/422, mientras la app Flutter y el dispositivo siguen usando `/api/v1` sin cambios.
