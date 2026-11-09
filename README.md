# FinaGotchi

Tamagotchi financiero por voz. El usuario le habla a un dispositivo ESP32, al simulador de escritorio o a la app Flutter, el backend transcribe el audio con IA, propone los movimientos y el usuario confirma antes de que se guarde.

**Integrantes:** Helen Andrea Lavao Benitez · Danna Michelle Guzman Angarita · Irene Charlotte Romero Avendaño
**Asignatura:** Desarrollo de Aplicaciones AV - Universidad de San Buenaventura

## Componentes

| Ruta | Qué es |
|---|---|
| `backend/` | API Flask + SQLite + IA. Endpoints, autenticación, reglas de negocio. |
| `backend/ai.py` | Proveedores de transcripción (faster-whisper local). |
| `backend/audio.py` | Validación del WAV que llega del dispositivo. |
| `backend/nlp.py` | Interpretación con LLM (Ollama/faster-whisper) y reglas locales de respaldo. |
| `backend/finance_engine.py` | Ingreso, gasto, colchón y capacidad de ahorro on-the-fly. |
| `backend/optimization.py` | Programación lineal del plan de metas y fallback greedy. |
| `database/` | Esquema SQL, vistas, seeds e inicializador. |
| `simulator/` | Simulador de escritorio que imita al dispositivo; incluye la opción `[P]` del plan. |
| `tests/` | Pruebas del esquema, la API y la optimización. |
| `tools/` | Utilidades, incluida la prueba real del flujo de voz. |
| `docs/` | Especificaciones, lógica de negocio, endpoints y detalle de la IO. |
| `frontend/` | App Flutter conectada al backend; funciona en macOS y en iPhone. |

## Puesta en marcha

### 1. Dependencias

```powershell
py -3 -m pip install -r requirements.txt
```

### 2. Configurar la IA (opcional)

El backend funciona **sin claves externas**: transcribe con faster-whisper
local e interpreta con Ollama si está corriendo. Ningún proveedor necesita
clave de API.

Para revisar el estado sin cambiar nada:

```powershell
py -3 tools/verificar_entorno.py
```

> El secreto de firma de tokens (`FINAGOTCHI_SECRET`) se configura solo via
> `backend/.env` (ignorado por git); `tests/test_seguridad.py` impide secretos reales en el repo.
>
> ```powershell
> [Environment]::SetEnvironmentVariable("FINAGOTCHI_SECRET", "un_secreto_largo", "User")
> ```

### 3. Base de datos

```powershell
py -3 database/init_db.py
```

### 4. Levantar el backend

```powershell
py -3 backend/server.py
```

Queda en `http://127.0.0.1:5001/api/v1`.

### 5. Simulador

```powershell
py -3 -m pip install -r requirements-simulator.txt
py -3 simulator/main.py
```

Ejecutar como administrador para que `keyboard` capture la tecla ESPACIO. Más detalles en `GUIA_SIMULADOR.md`.

### 6. Endpoints de consultas (Guia 4)

Capa de compatibilidad sobre Flask (sin cambiar el contrato `/api/v1`). Requiere `Authorization: Bearer <token>` (registrar primero como en §2). Devuelve JSON plano de Guia 4 (no el sobre `{ok,data}`).

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/health` | Salud del backend |
| `POST` | `/api/telemetry` | Persiste telemetría `device_id, timestamp, sequence, measurements, message_id` → 201 |
| `GET` | `/api/measurements` | Lista lecturas. Filtros: `device_id, limit (1-100), offset, from, to` (ISO8601 UTC) → 200 |
| `GET` | `/api/devices` | Lista dispositivos con lecturas (`measurement_count, last_timestamp`) |
| `GET` | `/api/devices/<device_id>` | Un dispositivo → 200; inexistente → 404 |
| `GET` | `/docs` | OpenAPI mínimo con los 5 paths |

Ejemplo mínimo:

```powershell
# tras registrar un usuario en /api/v1/auth/register y obtener access_token
$token = "TU_TOKEN"
curl.exe -H "Authorization: Bearer $token" -H "Content-Type: application/json" `
  -d '{"device_id":"FINA-001","sequence":1,"measurements":{"temp":25.5},"message_id":"msg-001"}' `
  http://localhost:5001/api/telemetry
curl.exe -H "Authorization: Bearer $token" -H "Content-Type: application/json" http://localhost:5001/api/measurements
```

Documentación y decisiones: `docs/decisiones/api-rest.md` y `docs/evidencias/guia-4/README.md`. Pruebas rápidas:

```powershell
py -3 -m unittest tests.test_api_queries
```

### Comandos que sí funcionan

Estos son los comandos del proyecto, verificados por `tests/test_comandos.py`, que levanta el backend y ejecuta el simulador tal como se documenta:

| Comando | Qué hace |
|---|---|
| `py -3 backend/server.py` | Levanta la API en el puerto 5000. |
| `py -3 simulator/main.py` | Abre el dispositivo simulado con su menú de pantallas. |
| `py -3 tools/configurar_voz.py` | Descarga e instala la voz local de Nancy en `%USERPROFILE%/.finagotchi/piper`. |
| `py -3 database/init_db.py` | Crea o actualiza la base de datos. |
| `py -3 -m unittest discover -s tests -v` | Corre todas las pruebas. |
| `py -3 tools/verificar_entorno.py` | Revisa dependencias, base, clave, IA y micrófono. |
| `py -3 tools/generar_dataset_bd.py` | Regenera los datos demo de `finagotchi.db` y exporta CSV. |
| `py -3 tools/exportar_csv_consolidado.py` | Exporta todas las tablas a un solo CSV para Excel. |
| `py -3 tools/grabar_dataset.py` | Graba los clips del dataset con el micrófono. |
| `py -3 tools/evaluar_dataset.py` | Evalúa el dataset (WER, montos, latencia). |
| `py -3 tools/probar_flujo_voz.py audio.wav` | Prueba el flujo de voz con un WAV. |

## Pruebas

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m compileall -q backend simulator tests
```

Al cierre de esta versión son **206 pruebas**. Incluyen esquema, API, audio, IA,
seguridad, codificación, simulador, el agente conversacional y la optimización
con programación lineal.

Con el backend levantado se puede probar el flujo completo con audio real:

```powershell
py -3 tools/probar_flujo_voz.py ruta\al\audio.wav
```

## Audio

- Formato aceptado: WAV, 16 kHz, mono, 16 bits.
- Duración: entre 0,5 y 40 segundos.
- Tamaño máximo: 2 MB.
- El audio se procesa en memoria y **no se guarda** ni en la base ni en disco.
- El backend guarda el texto, la duración y la auditoría de la llamada en `interacciones_ia`.

### Proveedores de transcripción

| Proveedor | Clave | Cuota | Latencia | Cuándo usarlo |
|---|---|---|---|---|
| `local` | no | ninguna | ~1 s | Único proveedor; siempre disponible, funciona sin internet. |

La transcripción es siempre con `faster-whisper` corriendo en el PC del
backend. El modelo elegido se configura con `STT_MODELO_LOCAL` (`tiny`,
`base`, `small`, `medium`, `large-v3`; por defecto `base`). No necesita
clave, ni cuota, ni conexión a internet: es la vía para demo y producción
offline.

### Modelo de IA que interpreta la frase

La transcripción solo devuelve texto. Quien decide **qué tipo de movimiento es, el monto, la categoría y la cuenta** es un modelo de lenguaje:

| Proveedor | Clave | Latencia | Notas |
|---|---|---|---|
| `ollama` | no | 2–8 s | Modelo local (qwen3:4b). Gratis, offline, sin cuota. |

Se instala con:

```powershell
winget install --id Ollama.Ollama --exact --silent
ollama pull qwen3:4b
```

La IA recibe el **catálogo real del usuario** (sus 16 categorías y sus cuentas) y debe responder con un JSON. Esa respuesta se **valida contra la base de datos**: si inventa una categoría que no existe, o dice una cuenta inexistente, se descarta ese campo y se usa el de la cuenta por defecto. Si no hay ningún LLM disponible, el sistema cae a las reglas por palabra clave de `backend/nlp.py`.

Para apagar la interpretación por IA y quedarte solo con las reglas: `NLP_USAR_IA=off`.

Además, la transcripción recibe las **hotwords** del usuario (los nombres de sus cuentas y categorías). Sin eso, Whisper escribe "por Nike" en vez de "por Nequi", y "con David Plata" en vez de "con Daviplata".

## Optimización de metas (Investigación de Operaciones)

El backend incluye un planificador de metas con **programación lineal**. Calcula
cuánto ahorrar en cada meta y en cada mes para maximizar el cumplimiento
ponderado por prioridad, respetando la capacidad mensual y las fechas límite.

- `GET /api/v1/goals/plan` devuelve el plan con los datos reales.
- `POST /api/v1/goals/plan/simulate` permite probar ingresos, gastos, capacidad y prioridades sin escribir en la base.
- `GET /api/v1/home?incluir_plan=1` agrega un resumen compacto.
- El simulador lo muestra con la opción `[P]`.

El plan **solo propone**: nunca crea transacciones, nunca mueve saldos y nunca
sustituye la confirmación humana. Se calcula en cada petición y no se persiste.
El detalle matemático, los contratos y los ejemplos están en
[`docs/OPTIMIZACION_IO.md`](docs/OPTIMIZACION_IO.md); el catálogo completo de
algoritmos está en [`docs/LOGICA_DE_NEGOCIO.md`](docs/LOGICA_DE_NEGOCIO.md).

## Dataset de evaluación

`datasets/eval_audio/manifest.csv` define 500 casos de prueba: montos en cifras y en palabras, millones, ingresos, gastos, ahorro, consultas, frases sin monto, ruido y acentos.

```powershell
py -3 tools/generar_dataset.py     # regenera y valida el manifiesto
py -3 tools/grabar_dataset.py     # graba los clips con el micrófono
py -3 tools/evaluar_dataset.py    # transcribe y calcula WER, montos y latencia
```

El manifiesto se actualiza con la duración de cada clip. Los audios no se versionan. El reporte queda en `datasets/eval_audio/reporte.json`.

Objetivos de la evaluación: WER menor a 15 %, montos exactos en al menos 90 % de los casos y latencia p95 menor a 5 segundos.

## Dataset de la base de datos

`finagotchi.db` viene cargada con un dataset sintético reproducible: 25 usuarios, 18 dispositivos (nunca más dispositivos que usuarios y máximo uno por usuario), 500 transacciones, metas, presupuestos, cierres, alertas, telemetría y casos límite.

```powershell
py -3 tools/generar_dataset_bd.py
py -3 tools/generar_dataset_bd.py --semilla 1234 --transacciones 200
py -3 tools/generar_dataset_bd.py --db C:\ruta\copia.db --no-exportar
```

El generador respalda la base en `backups/` antes de borrar los datos de prueba, conserva `plantilla_*` y `schema_migrations`, verifica `foreign_key_check`/`integrity_check` y deja el resultado en:

- `datasets/dataset_bd/csv/`: un CSV por tabla (UTF-8, sin BOM).
- `datasets/dataset_bd/consolidado/dataset_completo.csv`: todas las tablas en un solo CSV en formato largo, con UTF-8 con BOM y separador `;`.
- `datasets/dataset_bd/manifest.json`: conteo, tamaño y SHA-256 de cada archivo.
- `datasets/dataset_bd/README.md`: contenido y credenciales.

El consolidado se regenera aparte, sin tocar la base ni los 40 CSV:

```powershell
py -3 tools/exportar_csv_consolidado.py
py -3 tools/exportar_csv_consolidado.py --separador "," --sin-bom --omitir-vacios
```

Cuentas demo: `simulador@finagotchi.local` / `simulador123` y `demo01@finagotchi.local` … `demo24@finagotchi.local` / `Demo1234`.

## App Flutter

La app está **conectada al backend**. La URL se elige automáticamente según la
plataforma en `frontend/lib/services/api_config.dart`:

- macOS: `http://127.0.0.1:5001/api/v1`.
- Android/iOS: usa la IP del Mac en la red local. Se puede sobrescribir con
  `--dart-define=API_BASE_URL=...`.

En macOS:

```bash
cd frontend
flutter pub get
flutter run -d macos
```

En el iPhone físico (mismo Wi-Fi que el Mac y backend escuchando en `0.0.0.0`):

```bash
cd frontend
flutter run -d <UDID_DEL_IPHONE> \
  --dart-define=API_BASE_URL=http://192.168.1.22:5001/api/v1
```

Para instalar una versión que abra desde el icono (sin `flutter run`) hay que
compilar en release:

```bash
flutter build ios --release \
  --dart-define=API_BASE_URL=http://192.168.1.22:5001/api/v1
```

Pruebas de la app (no necesitan backend):

```bash
cd frontend
flutter test
```

`frontend/test/widget_test.dart` comprueba que el login se monta y valida
correo y contraseña.

## Base de datos

- SQLite con `PRAGMA foreign_keys = ON`.
- Esquema versionado en `database/sql/`; la versión vigente está en `database/init_db.py`.
- `fecha_hora` en UTC y `fecha_local` en `America/Bogota`.
- Solo las transacciones `confirmado` afectan balances, puntos, metas y salud.

## Documentación

- `docs/ESPECIFICACIONES.md`: contrato funcional, endpoints, esquema y decisiones.
- `docs/LOGICA_DE_NEGOCIO.md`: cómo funciona hoy la lógica de negocio en el código real, con fórmulas, invariantes y diferencias frente a la especificación.
- `docs/endpoints.md`: guía práctica para conectar la app Flutter con la API.
- `docs/DISPOSITIVO.md`: hardware, pinout, audio y flujos de pantalla para el firmware.
- `GUIA_SIMULADOR.md`: guía del simulador de escritorio.

