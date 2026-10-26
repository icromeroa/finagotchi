# Problemas conocidos

| # | Problema | Estado |
|---|---|---|
| 1 | En macOS el puerto 5000 está ocupado por AirPlay Receiver; el backend y el simulador usan el **8000**. | Resuelto |
| 2 | Si la transcripción falla ("Sin transcripción") o no trae número, el backend registra un gasto de $10.000 en `other`. | Pendiente |
| 3 | Las filas guardadas antes de la Guía 4 tienen `sequence` y `received_at` en `null`. | Aceptado |
| 4 | Swagger UI (`/docs`) carga sus archivos desde un CDN: requiere internet. | Aceptado |
| 5 | Filtro por rango de fechas (`from`/`to`) y total de registros en la paginación no implementados. | Pendiente |
| 6 | `finagotchi.db` está versionada en Git; conviene moverla a `.gitignore` más adelante. | Pendiente |
