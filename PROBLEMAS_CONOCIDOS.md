# Problemas conocidos

Estado al cierre de la Fase A (audio real con IA).

## Resueltos en esta fase

| Problema | Estado | Solución |
|---|---|---|
| El simulador transcribía en el PC con Google Speech Recognition | Resuelto | El simulador graba el WAV y lo envía al backend; transcribe Gemini Flash. |
| El backend no aceptaba audio | Resuelto | `POST /messages` y `POST /device/messages` aceptan `multipart/form-data` con el campo `audio`. |
| `STT_NO_CONFIGURADO` sin proveedor | Resuelto | `backend/ai.py` con Gemini Flash, configurable por `backend/.env`. |
| El límite de audio era de 30 segundos | Resuelto | Esquema v4 con CHECK de 0,5 a 40 segundos en `mensajes_dispositivo` y `dispositivos_telemetria`. |
| Los montos en palabras no se entendían | Resuelto | `backend/nlp.py` interpreta cifras y palabras, de `catorce mil` a `dos millones quinientos mil`. |
| Los montos en millones no se detectaban | Resuelto | El intérprete reconoce `millones` y `1.5 millones`. |
| El mensaje duplicado se procesaba dos veces | Resuelto | La idempotencia se valida antes de llamar al proveedor de transcripción. |
| El audio podía quedar almacenado | Resuelto | El audio se procesa en memoria y no se persiste en disco ni en la base. |
| La clave de Gemini podía subirse al repositorio | Resuelto | `.gitignore` excluye `backend/.env` y `*.db`. |
| Un `git clean -xdf` borró `backend/.env` y se perdió la clave | Resuelto | La clave ahora vive en `%USERPROFILE%\.finagotchi/gemini.env`, fuera del repo, con `tools/configurar_api_key.py`. `tests/test_seguridad.py` falla si una clave real entra al repo. |
| Se pegó la clave real en `backend/.env.example`, que sí está versionado | Resuelto | La prueba de seguridad lo detectó y lo limpió. La clave real solo puede vivir en el archivo externo o en una variable de entorno. |
| Google devolvió `401 ACCESS_TOKEN_TYPE_UNSUPPORTED` con la clave `AQ.Ab` | Resuelto con alternativa | Problema abierto de Google: desde el 28 de mayo de 2026 AI Studio solo emite "Auth keys" y hay incompatibilidades con `generativelanguage.googleapis.com`. Se agregó el proveedor local con faster-whisper, que no necesita clave ni cuota, y `STT_PROVEEDOR=auto` cae a él automáticamente. |
| La transcripción escribía las marcas mal ("por Nike", "con David Plata") | Resuelto | El backend manda los nombres de las cuentas y categorías del usuario como hotwords del modelo de transcripción. |
| Las reglas por palabra clave no alcanzaban para asignar categoría y cuenta | Resuelto | Se agregó la interpretación con modelo de lenguaje (Ollama con `qwen3:4b`, o Gemini). La respuesta del modelo se valida contra el catálogo real del usuario y lo que no cuadra se completa con las reglas. |
| La interpretación por IA dejaba movimientos sin categoría y violaba el CHECK del esquema | Resuelto | Todo movimiento distinto de ahorro recibe la categoría de último recurso ("Otros" / "Otros ingresos"). Además la API ya responde JSON en el error 500 en vez de la página de depuración de Flask. |

## Abiertos

| Problema | Impacto | Plan |
|---|---|---|
| El modelo `gemini-3.8-flash` responde `503` por demanda alta | Transcripción intermitente | Cadena de modelos de respaldo (`GEMINI_MODEL_FALLBACKS`) y reintento con backoff. Implementado. |
| La capa gratuita limita a 3 peticiones por minuto y por modelo | El dataset de 500 clips necesita pausas | `tools/evaluar_dataset.py` espera entre clips y reintenta ante `429`. |
| La capa gratuita sube la latencia de transcripción a 16–18 s cuando se agota la cuota | El usuario espera demasiado ante el dispositivo | Con la API en reposo la latencia es de 3–5 s. Para producción se recomienda cuenta de pago o un STT dedicado. |
| Un mensaje con dos transacciones solo genera una | Se pierde parte de la información | El esquema ya soporta varias transacciones por mensaje; falta la segmentación en `backend/nlp.py`. |
| La app Flutter no tiene capa HTTP | El frontend no consume la API | Fase B: cliente HTTP, tokens, login, onboarding y pantalla de voz. |
| No existe firmware de la ESP32 | El dispositivo físico no funciona | Fase C: grabación I2S, envío por Wi-Fi, polling de notificaciones y pantalla. |
| La ESP32 no puede guardar 40 s de WAV en SRAM | Límite físico | Streaming por Wi-Fi o cola temporal en flash. Decisión de firmware pendiente. |
| BLE sin implementar | Solo configuración | El MVP usa Wi-Fi; BLE queda para la vinculación inicial. |
| Endpoints de app documentados pero no implementados | `/notifications`, `/trash`, `/transactions/bulk-confirm`, `/device/commands` | Fase B: implementarlos o retirarlos de la documentación. |
| `docs/ESPECIFICACIONES.md` usa `/metrics/diagnosis` | El backend expone `/metrics/diagnostics` | Corregir la documentación en la fase B. |
| El dataset real todavía no está grabado | No hay línea base con voz humana | `tools/grabar_dataset.py` graba los 500 clips del manifiesto. |
