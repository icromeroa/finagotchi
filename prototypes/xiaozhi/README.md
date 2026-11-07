# Prototipo Xiaozhi + FinaGotchi

Prototipo **aislado** para probar si Xiaozhi puede aportar wake word, AFE, STT y
TTS al dispositivo FinaGotchi. **No reemplaza el backend** ni cambia el esquema
de la base. El firmware propio sigue fuera de alcance hasta cerrar este
prototipo.

- Firmware de referencia: [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32)
- Servidor de referencia: [xinnan-tech/xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server)
- Documentación de MCP de Xiaozhi: [mcp-endpoint-integration.md](https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/mcp-endpoint-integration.md)

## 1. Decisión de arquitectura

Xiaozhi se usa como **capa de voz**; FinaGotchi sigue siendo la **fuente de
verdad financiera**.

```text
┌─────────────────────────────┐
│ ESP32-S3 (Xiaozhi)          │
│  wake word "Nancy" + AFE    │
│  INMP441 -> STT             │
│  MAX98357A <- TTS           │
└──────────────┬──────────────┘
               │ WebSocket / MCP
┌──────────────▼──────────────┐
│ Servidor Xiaozhi            │
│  STT español (Whisper/Vosk) │
│  LLM + tool calling         │
│  TTS personalizado          │
└──────────────┬──────────────┘
               │ POST /turno
               │ POST /sintetizar
┌──────────────▼──────────────┐
│ bridge.py (este prototipo)  │
│  traduce texto -> contrato  │
│  de dispositivo FinaGotchi  │
└──────────────┬──────────────┘
               │ X-Device-Token
┌──────────────▼──────────────┐
│ Backend FinaGotchi          │
│  conversación, fechas,      │
│  confirmación y datos       │
└─────────────────────────────┘
```

Regla clave: Xiaozhi **no decide** montos, fechas ni confirmaciones. Solo
transcribe, invoca la herramienta y reproduce la frase que devuelve FinaGotchi.

## 2. Componentes

| Archivo | Para qué |
|---|---|
| `bridge.py` | Puente HTTP sin dependencias externas. Expone `/turno`, `/confirmar`, `/sintetizar` y `/salud`. |
| `provisionar.py` | Registra un `device_uid`, lo vincula a una cuenta y obtiene `device_token` por HTTP. |
| `mcp_servidor.py` | Herramienta MCP `finagotchi_turno` para que Xiaozhi llame al puente. |
| `cliente_prueba.py` | Prueba el puente sin placas ni servidor Xiaozhi; opcionalmente reproduce la voz. |
| `config.example.json` | Plantilla de configuración. Copia los valores a `config.local.json`. |
| `.config.yaml.example` | Plantilla de Xiaozhi (STT Whisper, LLM con function_call, TTS Edge/custom Nancy). Copiar fuera del repo como `data/.config.yaml`. |
| `test_bridge.py` | Pruebas unitarias del puente con HTTP simulado. |

## 3. Requisitos

- Backend FinaGotchi corriendo en `http://127.0.0.1:5000`.
- Python 3.10+ (el proyecto usa 3.14 en Windows).
- Para el módulo MCP: `pip install "mcp[cli]"`.
- Para la prueba de voz en Windows: `winsound` viene con Python.
- Para Xiaozhi completo: servidor Xiaozhi con STT/TTS en español y la placa
  ESP32-S3 SuperMini con PSRAM (16 MB flash), INMP441, MAX98357A, TFT 240x320 y
  3 botones. El pinout no se duplica aquí: ver `docs/DISPOSITIVO.md`.

## 4. Puesta en marcha

### 4.1 Levantar el backend

En la raíz del repositorio FinaGotchi:

```powershell
py -3 backend/server.py
```

### 4.2 Obtener el token del dispositivo

Copia la plantilla y ejecuta el provisionamiento. El script inicia sesión; si la
cuenta no existe, la registra.

```powershell
Copy-Item prototypes/xiaozhi/config.example.json prototypes/xiaozhi/config.local.json
py -3 prototypes/xiaozhi/provisionar.py --correo simulador@finagotchi.local
```

El script pide la contraseña, registra `FINAGOTCHI-XIAOZHI-01`, obtiene el PIN,
lo vincula y escribe `device_token` en `config.local.json`.

> `config.local.json` está en `.gitignore`. Nunca lo subas ni pegues el token en
> capturas, issues o documentación.

Para una cuenta existente del simulador puedes usar
`--password simulador123`. Para un dispositivo ya vinculado, usa otro
`--device-uid` o desvincúlalo primero desde la app.

### 4.3 Arrancar el puente

```powershell
py -3 prototypes/xiaozhi/bridge.py
```

Por defecto escucha en `http://127.0.0.1:8787` y lee
`prototypes/xiaozhi/config.local.json`. También acepta variables de entorno:

| Variable | Default |
|---|---|
| `FINAGOTCHI_BASE_URL` | `http://127.0.0.1:5000/api/v1` |
| `FINAGOTCHI_DEVICE_TOKEN` | vacío |
| `XIAOZHI_BRIDGE_HOST` | `127.0.0.1` |
| `XIAOZHI_BRIDGE_PORT` | `8787` |
| `FINAGOTCHI_TIMEOUT_S` | `90` |

Si Xiaozhi corre en otra máquina o contenedor, escucha en la interfaz de LAN y
limita el puerto con el firewall:

```powershell
py -3 prototypes/xiaozhi/bridge.py --host 0.0.0.0
```

No expongas el puente a Internet: el token del dispositivo da acceso a la cuenta.

### 4.4 Probar sin Xiaozhi

```powershell
py -3 prototypes/xiaozhi/cliente_prueba.py "gasté 20 mil en almuerzo"
py -3 prototypes/xiaozhi/cliente_prueba.py "sí"
py -3 prototypes/xiaozhi/cliente_prueba.py "¿cuánto gasté ayer?" --voz
```

El cliente muestra:

- `NANCY (voz)`: el resumen corto (`texto_voz` / `hablar`).
- `NANCY (pantalla)`: el detalle con cifras formateadas (`mensaje_nancy`).
- `tipo` y `requiere_confirmacion`.

La confirmación se hace con el mismo `/turno`: escribe `"sí"` o `"no"`. El
estado conversacional vive en FinaGotchi y se identifica por el `device_token`.

### 4.5 Pruebas unitarias

```powershell
py -3 -m unittest discover -s prototypes/xiaozhi -p "test_*.py" -v
```

No necesitan backend ni red: simulan las respuestas HTTP.

## 5. Integración con Xiaozhi

### 5.1 STT

Configura el proveedor de STT del servidor Xiaozhi para español (Whisper local,
Vosk o el proveedor que ya uses). El puente **no recibe audio**: recibe texto ya
transcrito. Así se evita duplicar el STT y se mantiene el prototipo pequeño.

### 5.2 MCP: herramienta `finagotchi_turno`

1. Habilita el endpoint MCP en tu servidor Xiaozhi y copia la URL
   `ws://.../mcp_endpoint/mcp/?token=...`.
2. Instala la dependencia en el entorno del pipe: `pip install "mcp[cli]"`.
3. Ejecuta el pipe de Xiaozhi apuntando a este módulo. El ejemplo oficial usa
   `mcp_pipe.py`:

   ```powershell
   $env:MCP_ENDPOINT = "ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=..."
   $env:XIAOZHI_BRIDGE_URL = "http://127.0.0.1:8787"
   python mcp_pipe.py mcp_servidor.py
   ```

4. En el agente de Xiaozhi, instruye al modelo:

   > Cuando el usuario hable de gastos, ingresos, ahorros, metas o consultas
   > financieras, llama a `finagotchi_turno` con la frase textual. Di
   > literalmente el campo `respuesta` del resultado. No inventes montos ni
   > fechas. Si `requiere_confirmacion` es verdadero, espera la respuesta del
   > usuario y vuelve a llamar a `finagotchi_turno` con esa respuesta ("sí",
   > "no", "cancela" o una corrección).

La herramienta devuelve un JSON compacto:

```json
{
  "respuesta": "¿Registro un gasto de 20 mil pesos en almuerzo?",
  "detalle": "¿Registro un gasto de $20.000 en Alimentación desde Efectivo? ...",
  "tipo_respuesta": "confirmacion",
  "requiere_confirmacion": true,
  "intent": "registrar",
  "ok": true
}
```

`respuesta` es lo que se debe pronunciar; `detalle` es lo que se muestra en
pantalla.

### 5.3 TTS: voz de FinaGotchi

El servidor Xiaozhi puede usar su TTS habitual o un TTS personalizado que llame
al puente para conservar la voz de Nancy (Piper `es_MX`):

```yaml
# Ejemplo de proveedor TTS personalizado en Xiaozhi.
TTS:
  selected_module: FinaGotchi
  FinaGotchi:
    type: custom
    method: POST
    url: "http://127.0.0.1:8787/sintetizar"
    params:
      input: "{prompt_text}"
    headers:
      Content-Type: "application/json"
```

El puente acepta `texto`, `prompt_text`, `input` o `text` como nombre del campo.
Devuelve `audio/wav` directamente, sin guardarlo. Verifica en tu versión de
Xiaozhi si el proveedor `custom` espera un archivo binario o un enlace de
descarga; si espera enlace, adapta el proveedor o usa el TTS nativo de Xiaozhi.

### 5.4 Wake word

Configura la wake word **“Nancy”** en el firmware Xiaozhi. La placa tiene PSRAM
confirmada, así que el AFE y la wake word son viables. Ajusta el modelo de wake
word y prueba falsos positivos en un cuarto con ruido antes de la fase de
firmware.

## 6. Contrato que se conserva

El puente no inventa un contrato nuevo: reutiliza el de FinaGotchi.

| Campo | Uso en Xiaozhi |
|---|---|
| `texto_voz` / `hablar` | Frase corta para TTS. |
| `mensaje_nancy` | Texto completo para pantalla. |
| `tipo_respuesta` | `confirmacion`, `resultado`, `consulta`, `aclaracion`, `ayuda`, `error`. |
| `requiere_confirmacion` | Si es `true`, el agente debe esperar la respuesta natural. |
| `intent` | Intención detectada (`registrar`, `consultar_movimientos`, ...). |
| `datos` | Rango, resumen y movimientos para la pantalla. |

FinaGotchi sigue resolviendo fechas, montos, confirmaciones y persistencia. El
audio nunca se persiste.

## 7. Seguridad

- El `device_token` es equivalente a la sesión del dispositivo: trátalo como
  contraseña.
- `config.local.json` no se versiona. Verifica con `git status` antes de cada
  commit.
- El puente escucha en `127.0.0.1` por defecto. Si lo abres a la LAN, usa
  firewall y no lo publiques en Internet.
- No hay claves de Gemini ni de otros proveedores en este prototipo.
- El puente no acepta audio ni escribe WAV; solo reenvía texto y reproduce/entrega
  audio en memoria.

## 8. Limitaciones conocidas

- **No es firmware todavía.** No se flashea la placa ni se toca `frontend/`.
- El puente no hace STT; eso queda en Xiaozhi.
- La integración MCP se validó a nivel HTTP y de módulo, pero el end-to-end con
  un servidor Xiaozhi real requiere desplegarlo aparte.
- El proveedor TTS `custom` de Xiaozhi puede variar entre versiones; el ejemplo
  de YAML es una guía, no una garantía de compatibilidad.
- Si el backend se reinicia, se pierde el hilo conversacional en memoria (TTL de
  30 minutos), pero los movimientos confirmados siguen en la base.
- El prototipo no cambia el esquema ni crea migraciones.

## 9. Siguientes pasos

1. Desplegar Xiaozhi en un directorio/repositorio aparte (no vendorizarlo aquí).
2. Configurar STT español y TTS personalizado hacia `/sintetizar`.
3. Conectar `mcp_servidor.py` con el endpoint MCP y probar el flujo completo.
4. Flashear la ESP32-S3 con Xiaozhi, wake word “Nancy”, y medir latencia.
5. Decidir si Xiaozhi reemplaza el firmware propio o solo aporta wake word/AFE.
6. Recién entonces iniciar la fase de firmware.

## 10. Checklist del prototipo

- [x] Puente HTTP aislado hacia FinaGotchi.
- [x] Provisionamiento de `device_token`.
- [x] Módulo MCP `finagotchi_turno`.
- [x] Cliente de prueba con voz opcional.
- [x] Pruebas unitarias del puente.
- [x] Prueba del puente contra el backend real (ver `docs/PRUEBA_PUENTE.md`).
- [x] Documentación de instalación Docker y configuración (ver `docs/`).
- [ ] Prueba end-to-end con servidor Xiaozhi real.
- [ ] Prueba en la placa ESP32-S3 con INMP441 y MAX98357A.
- [ ] Decisión de arquitectura para la fase de firmware.

## 11. Documentación detallada

| Documento | Contenido |
|---|---|
| `docs/PRUEBA_PUENTE.md` | Evidencia de la prueba X0 (2026-11-06) con backend real |
| `docs/INSTALL_XIAOZHI.md` | Instalación del servidor mínimo con Docker |
| `docs/CONFIG_XIAOZHI.md` | Configuración ASR/LLM/TTS/MCP para FinaGotchi |
| `docs/END_TO_END.md` | Flujo completo y guión de prueba MCP |
| `docs/PRODUCTION_PORTABLE.md` | Brecha prototipo ↔ producción y riesgos |
