# Evidencias Guia 4 (índice)

Carpeta generada en ejecución de la opción B. El contenido sintetiza el porqué y dónde están las pruebas.

- A0 Checkpoint — backend responde `/health` 200 y persiste mensajes.
- A1 Diseño API — ver `docs/decisiones/api-rest.md` (tabla de recursos, filtros y límites).
- A2 GET /api/measurements — test `test_post_telemetry_201_and_listed` (201 y luego lista con `device_id`, `sequence`, `measurements`).
- A3 Dispositivos — `GET /api/devices`, `GET /api/devices/<id>` real y 404 con NO-EXISTE (`test_unknown_device_404`).
- A4 Filtros/paginación — `test_limit_restricts_count` y `test_device_id_filters`.
- A5 Históricos — filtro `from/to` ISO8601 sobre `recibido_en` (UTC) en `compat_get_measurements`.
- A6 Pruebas manuales — matriz en `docs/decisiones/api-rest.md`: 200 / 404 / 422 documentados por código y prueba.
- A7 Integración — trazabilidad por `message_id` (POST → SQLite → GET) en `test_post_telemetry_201_and_listed`.
- A8 Automáticas — `tests/test_api_queries.py` (5 pruebas: 201, límite, filtro, 404, 422).
- A9 Revisión — checklist de reproducible: registro de usuario, POST, GET list, GET devices, 404, 422.

```powershell
py -3 -m unittest tests.test_api_queries
py -3 -m compileall -q backend tests
```
