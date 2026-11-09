# Flujo end-to-end con Xiaozhi

```text
ESP32-S3 (wake word + AFE + Opus)
  → Servidor Xiaozhi (VAD Silero → Whisper STT)
  → LLM (Groq) con Intent function_call
  → Herramienta MCP finagotchi_turno
  → bridge.py (http://127.0.0.1:8787/turno)
  → Backend FinaGotchi /device/messages (X-Device-Token)
  → {texto_voz, mensaje_nancy, requiere_confirmacion}
  → TTS (EdgeTTS → luego /sintetizar Piper es-MX)
  → MAX98357A
```

## 1. Arranque ordenado

```powershell
# 1) Backend
py -3 backend/server.py

# 2) Puente
py -3 prototypes/xiaozhi/bridge.py --host 127.0.0.1 --port 8787

# 3) Tanner Xiaozhi (Docker)
cd C:\Users\ASUS\xiaozhi-server
docker compose up -d
docker logs -f xiaozhi-esp32-server   # apunta OTA + MCP endpoint ws://
```

## 2. MCP (`mcp_servidor.py`)

```powershell
$env:MCP_ENDPOINT = "ws://<IP>:8004/mcp_endpoint/mcp/?token=DelLog"
$env:XIAOZHI_BRIDGE_URL = "http://127.0.0.1:8787"
cd "G:\...\prototypes\xiaozhi"
py -3 mcp_servidor.py
```

El módulo expone:

| Herramienta | Entrada | Salida |
|---|---|---|
| `finagotchi_turno(texto)` | frase transcrita (“gasté 20 mil…”, “sí”, “¿cuánto gasté ayer?”) | `{respuesta, detalle, tipo_respuesta, requiere_confirmacion, intent, ok}` |
| `finagotchi_salud()` | — | estado de `/salud` |

## 3. Guión de prueba

| # | Decir | Esperado |
|---|---|---|
| 1 | “gasté 20 mil en almuerzo” | Nancy: “¿Registro un gasto de 20 mil pesos en almuerzo?” (`confirmacion`) |
| 2 | “sí” | “Listo. Guardé un gasto de 20 mil pesos…” |
| 3 | “¿cuánto gasté ayer?” | Resumen hablado + lista en pantalla; rango `ayer` |
| 4 | “cancela” (tras una confirmación) | Sin cambio de dinero; pendiente invalidado |

## 4. Fallos típicos

| Síntoma | Causa | Acción |
|---|---|---|
| LLM no llama a la herramienta | LLM sin `function_call` o `Intent != function_call` | Cambiar LLM y a `function_call` |
| `PUENTE_NO_DISPONIBLE` | Puente apagado o URL mal puesta | `curl http://127.0.0.1:8787/salud` |
| TTS custom vacío | `host.docker.internal` mal o contrato JSON distinto | Primero `EdgeTTS`, luego revisar `/sintetizar` |
| STT no transcribe español | ASR local `FunASR` por defecto | Pasar a `GroqASR` / `OpenaiASR` |
| STT transcribe “哪里” en vez de español | Modelo local chino | Misma solución anterior |

## 5. Qué queda fuera

- Sin placa: usar la página de prueba web de Xiaozhi o un cliente software.
- Sin wake word “Nancy”: usar la por defecto o disparo manual.
- Sin firmware: nada de ESP-IDF hasta que este flujo sea verde.
