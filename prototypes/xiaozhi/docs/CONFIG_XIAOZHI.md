# Configuración de Xiaozhi para FinaGotchi

Plantilla completa en `prototypes/xiaozhi/.config.yaml.example`. Copiada como `data/.config.yaml` dentro de `C:\Users\ASUS\xiaozhi-server`.

## 1. Dónde se edita

| Archivo | Para qué |
|---|---|
| `prototypes/xiaozhi/.config.yaml.example` | Plantilla versionada (sin claves reales) |
| `C:\Users\ASUS\xiaozhi-server\data\.config.yaml` | Copia local con tus claves |
| `prototypes/xiaozhi/config.local.json` | `device_token` de FinaGotchi (ignorado por Git) |

> Xiaozhi **prioriza** `data/.config.yaml` sobre `config.yaml` del contenedor. Nunca edites el `config.yaml` del repo oficial.

## 2. Módulos seleccionados

```yaml
selected_module:
  VAD: SileroVAD          # local, sin clave
  ASR: GroqASR            # Whisper API en español (Groq)
  LLM: GroqLLM            # tool-calling gratuito
  VLLM: ChatGLMVLLM       # visión (opcional)
  TTS: EdgeTTS            # primero: es-MX sin clave
  Memory: nomem           # sin historial de Xiaozhi (el estado vive en FinaGotchi)
  Intent: function_call   # obligatorio para MCP
```

## 3. ASR en español (por qué Whisper API)

El default `FunASR` / `SenseVoiceSmall` soporta `zh/en/ja/ko/yue` y funciona flojo en español largo. `GroqASR` (`type: openai`) usa Whisper y transcribe español nativo sin modelo local:

```yaml
ASR:
  GroqASR:
    type: openai
    api_key: "TU_GROQ_API_KEY"
    base_url: "https://api.groq.com/openai/v1/audio/transcriptions"
    model_name: "whisper-large-v3-turbo"
```

- Registro gratis con Google: `https://console.groq.com/keys`
- Alternativa pagada: `OpenaiASR` con `gpt-4o-mini-transcribe`.

## 4. LLM con `function_call` (sin esto no hay MCP)

```yaml
LLM:
  GroqLLM:
    type: openai
    api_key: "TU_GROQ_API_KEY"
    base_url: "https://api.groq.com/openai/v1"
    model_name: "llama-3.3-70b-versatile"
    temperature: 0.7
    max_tokens: 500
```

> Hay que usar un modelo con tool-calling real. El mismo `config.yaml` oficial aclara que `Intent: function_call` exige LLM con `function_call`.

Alternativa gratuita: `ChatGLMLLM` (`glm-4-flash`, registro en `https://bigmodel.cn/usercenter/proj-mgmt/apikeys`).

## 5. TTS: EdgeTTS primero, Nancy después

### 5.1 Primera pasada (probada, sin clave)

```yaml
TTS:
  EdgeTTS:
    type: edge
    voice: es-MX-DaliaNeural
```

### 5.2 Voz de Nancy (Piper `es-MX`)

```yaml
TTS:
  FinaGotchiTTS:
    type: custom
    method: POST
    url: "http://host.docker.internal:5000/api/v1/device/voice/synthesize"
    params:
      texto: "{prompt_text}"
    headers:
      Content-Type: "application/json"
      X-Device-Token: "TU_DEVICE_TOKEN"
```

**Importante sobre `host.docker.internal`:** dentro de Docker, `127.0.0.1` es el contenedor, no tu Windows. Para llegar a FinaGotchi (que corre en Windows `5000`) usa `host.docker.internal` o la IP LAN de la PC.

Si el proveedor `custom` espera otro formato (JSON con `prompt_text` vs `texto`, o devuelve un enlace en vez de WAV), adaptar el bloque con lo que devuelva `/sintetizar` (`audio/wav` directo, sin persistir).

## 6. Prompt de Nancy

El `prompt` base en `config.yaml` viene en chino y con personalidad taiwanesa. Reemplázalo (ver `.config.yaml.example`):

```yaml
prompt: |
  Eres Nancy, asistente de voz de FinaGotchi, un finanzas personales en español de Latinoamérica.
  Nunca decides montos, fechas ni confirmaciones.
  Para cualquier gasto, ingreso, ahorro, meta o consulta financiera, llama a finagotchi_turno con la frase textual del usuario.
  Di literalmente el campo "respuesta" del resultado y no inventes cifras.
  Si "requiere_confirmacion" es true, espera la respuesta natural (sí/no/cancela/corrección) y vuelve a llamar a finagotchi_turno.
```

## 7. Wake words

Por defecto:

```yaml
wakeup_words:
  - "你好小智"
  - "小爱同学"
```

**No usar en la primera prueba.** La wake word “Nancy” requiere generar un modelo KWS (sherpa-onnx) y es una fase posterior. En la primera prueba se dispara con el botón/web o con la wake word por defecto.

## 8. Resumen de claves necesarias

| Clave | Para qué | Dónde se registra |
|---|---|---|
| `TU_GROQ_API_KEY` | ASR + LLM | `https://console.groq.com/keys` (Google) |
| `TU_DEVICE_TOKEN` | Solo si se usa el TTS custom | `prototypes/xiaozhi/config.local.json` |
| Ninguna | VAD, EdgeTTS, MCP | — |

Nunca pongas estas claves en Git, en este archivo de ejemplo ni en capturas.
