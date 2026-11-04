# FinaGotchi

Tamagotchi financiero por voz. El usuario le habla a un dispositivo ESP32 o al simulador de escritorio, el backend transcribe el audio con IA, propone los movimientos y el usuario confirma antes de que se guarde.

## Componentes

| Ruta | Qué es |
|---|---|
| `backend/` | API Flask + SQLite + IA. Endpoints, autenticación, reglas de negocio. |
| `backend/ai.py` | Proveedor de transcripción (Gemini Flash). |
| `backend/audio.py` | Validación del WAV que llega del dispositivo. |
| `backend/nlp.py` | Reglas locales para montos, categorías y cuentas. |
| `database/` | Esquema SQL, vistas, seeds e inicializador. |
| `simulator/` | Simulador de escritorio que imita al dispositivo. |
| `tests/` | Pruebas del esquema y de la API. |
| `tools/` | Utilidades, incluida la prueba real del flujo de voz. |
| `docs/` | Especificación funcional y especificación del dispositivo. |
| `frontend/` | App Flutter (pendiente de capa HTTP). |

## Puesta en marcha

### 1. Dependencias

```powershell
py -3 -m pip install -r requirements.txt
```

### 2. Configurar la IA

La API key **vive fuera del repositorio**, en `%USERPROFILE%\.finagotchi\gemini.env`. Así ningún `git clean -xdf`, borrado de carpeta o reinstalación del proyecto puede borrarla.

```powershell
py -3 tools/configurar_api_key.py
```

El asistente pide la clave (no se muestra mientras la escribes), la guarda en el archivo externo y la verifica contra la API real de Google. La clave se genera en <https://aistudio.google.com> → *Get API key*.

Para revisar el estado sin cambiar nada:

```powershell
py -3 tools/verificar_entorno.py
```

> **Nunca escribas la clave en `backend/.env.example`**: ese archivo sí está versionado en git y terminaría publicada en GitHub. `tests/test_seguridad.py` falla si detecta una clave real en cualquier archivo del repo.
>
> Si prefieres una variable de entorno en vez del archivo externo, también funciona y tiene prioridad sobre todo lo demás:
>
> ```powershell
> [Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "tu_clave", "User")
> ```

### 3. Base de datos

```powershell
py -3 database/init_db.py
```

### 4. Levantar el backend

```powershell
py -3 backend/server.py
```

Queda en `http://127.0.0.1:5000/api/v1`.

### 5. Simulador

```powershell
py -3 -m pip install -r requirements-simulator.txt
py -3 simulator/main.py
```

Ejecutar como administrador para que `keyboard` capture la tecla ESPACIO. Más detalles en `GUIA_SIMULADOR.md`.

### Comandos que sí funcionan

Estos son los comandos del proyecto, verificados por `tests/test_comandos.py`, que levanta el backend y ejecuta el simulador tal como se documenta:

| Comando | Qué hace |
|---|---|
| `py -3 backend/server.py` | Levanta la API en el puerto 5000. |
| `py -3 simulator/main.py` | Abre el dispositivo simulado con su menú de pantallas. |
| `py -3 database/init_db.py` | Crea o actualiza la base de datos. |
| `py -3 -m unittest discover -s tests -v` | Corre todas las pruebas. |
| `py -3 tools/verificar_entorno.py` | Revisa dependencias, base, clave, IA y micrófono. |
| `py -3 tools/grabar_dataset.py` | Graba los clips del dataset con el micrófono. |
| `py -3 tools/evaluar_dataset.py` | Evalúa el dataset (WER, montos, latencia). |
| `py -3 tools/probar_flujo_voz.py audio.wav` | Prueba el flujo de voz con un WAV. |

## Pruebas

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m compileall -q backend simulator tests
```

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
| `gemini` | sí | 3 peticiones/min en la capa gratuita | 3–5 s | Cuentas con una API key Standard (`AIza`). |
| `local` | no | ninguna | ~1 s | Siempre disponible, funciona sin internet. |

`STT_PROVEEDOR=auto` (por defecto) intenta Gemini y, si la clave está rota, no hay cuota o el proveedor falla, cae al modelo local de `faster-whisper` corriendo en el PC del backend. La caída queda registrada en `interacciones_ia` y la respuesta indica qué proveedor se usó.

El modelo local no necesita clave, ni cuota, ni conexión a internet: es la vía garantizada para una demo.

### Modelo de IA que interpreta la frase

La transcripción solo devuelve texto. Quien decide **qué tipo de movimiento es, el monto, la categoría y la cuenta** es un modelo de lenguaje:

| Proveedor | Clave | Latencia | Notas |
|---|---|---|---|
| `ollama` | no | 2–8 s | Modelo local (qwen3:4b). Gratis, offline, sin cuota. |
| `gemini` | sí | 1–3 s | Solo si la API key funciona. |

Se instala con:

```powershell
winget install --id Ollama.Ollama --exact --silent
ollama pull qwen3:4b
```

La IA recibe el **catálogo real del usuario** (sus 16 categorías y sus cuentas) y debe responder con un JSON. Esa respuesta se **valida contra la base de datos**: si inventa una categoría que no existe, o dice una cuenta inexistente, se descarta ese campo y se usa el de la cuenta por defecto. Si no hay ningún LLM disponible, el sistema cae a las reglas por palabra clave de `backend/nlp.py`.

Para apagar la interpretación por IA y quedarte solo con las reglas: `NLP_USAR_IA=off`.

Además, la transcripción recibe las **hotwords** del usuario (los nombres de sus cuentas y categorías). Sin eso, Whisper escribe "por Nike" en vez de "por Nequi", y "con David Plata" en vez de "con Daviplata".

## Dataset de evaluación

`datasets/eval_audio/manifest.csv` define 500 casos de prueba: montos en cifras y en palabras, millones, ingresos, gastos, ahorro, consultas, frases sin monto, ruido y acentos.

```powershell
py -3 tools/generar_dataset.py     # regenera y valida el manifiesto
py -3 tools/grabar_dataset.py     # graba los clips con el micrófono
py -3 tools/evaluar_dataset.py    # transcribe y calcula WER, montos y latencia
```

El manifiesto se actualiza con la duración de cada clip. Los audios no se versionan. El reporte queda en `datasets/eval_audio/reporte.json`.

Objetivos de la evaluación: WER menor a 15 %, montos exactos en al menos 90 % de los casos y latencia p95 menor a 5 segundos.

## App Flutter

La app ya habla con el backend: la capa HTTP está en `frontend/lib/api/`.

```powershell
cd frontend
flutter pub get
flutter run
```

La dirección del backend se resuelve sola (`127.0.0.1` en web y escritorio, `10.0.2.2` en el emulador de Android). Para apuntar a otro equipo:

```powershell
flutter run --dart-define=API_BASE_URL=http://192.168.1.7:5000/api/v1
```

Qué ya está conectado:

| Parte | Qué hace |
|---|---|
| `frontend/lib/api/api_client.dart` | Cliente HTTP con token, refresco automático y manejo de errores del backend. |
| `frontend/lib/api/grabador.dart` | Graba PCM de 16 kHz mono y lo envuelve en un WAV, que es lo que acepta el backend. |
| `frontend/lib/screens/login_screen.dart` | Inicio de sesión y registro reales contra la API. |
| `frontend/lib/screens/home_screen.dart` | Carga el resumen del día real y manda la voz al backend para que la transcriba e interprete. |

En web el navegador solo ofrece webm/opus, que el backend no acepta: ahí la app lo avisa y ofrece escribir la frase a mano. La voz funciona en Android e iOS.

El paso de **vincular el dispositivo** se puede saltar con el botón "Ahora no", que lleva directo al home. El vínculo se puede hacer después.

Si la app en Chrome no se conecta, revisa que el backend esté corriendo. El backend responde con el permiso de red privada que Chrome exige para hablar con un servidor local.

Pruebas de la app (necesitan el backend levantado):

```powershell
cd frontend
flutter test
```

## Base de datos

- SQLite con `PRAGMA foreign_keys = ON`.
- Esquema versionado en `database/sql/`; la versión vigente está en `database/init_db.py`.
- `fecha_hora` en UTC y `fecha_local` en `America/Bogota`.
- Solo las transacciones `confirmado` afectan balances, puntos, metas y salud.

## Documentación

- `docs/ESPECIFICACIONES.md`: contrato funcional, endpoints, esquema y decisiones.
- `docs/endpoints.md`: guía práctica para conectar la app Flutter con la API.
- `docs/DISPOSITIVO.md`: hardware, pinout, audio y flujos de pantalla para el firmware.
- `GUIA_SIMULADOR.md`: guía del simulador de escritorio.
