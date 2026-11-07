# Instalación de Xiaozhi autoalojado (mínimo) en Windows

> **Alcance:** solo `xiaozhi-server` (puertos `8000` y `8003`). Sin MySQL, Redis, Java ni panel web.
> **Carpeta fuera del repo:** `C:\Users\ASUS\xiaozhi-server` (ejemplo). Nunca dentro de `finagotchi/`.
> **Estado actual (2026-11-06):** verificado que la PC **no** tiene Docker, WSL, conda ni ffmpeg. Hay que instalarlos.

## 1. Requisitos previos

| Componente | Estado | Acción |
|---|---|---|
| Docker Desktop + WSL2 | No instalado | Instalar (ver abajo) |
| Cuenta Google | Sí | Para Groq (ASR+LLM gratis) y Zhipu |
| Clave LLM | No | Registrarse en Groq `console.groq.com` **o** Zhipu `bigmodel.cn` |
| Puertos `8000`, `8003`, `8787` | Libres | No tocar `5000` (backend corriendo) |

### 1.1 Instalar WSL2 + Docker Desktop

1. PowerShell **como administrador**:

   ```powershell
   wsl --install
   ```

2. Reiniciar la PC (obligatorio tras WSL2).
3. Instalar Docker Desktop desde `https://www.docker.com/products/docker-desktop`.
4. Abrir Docker Desktop y esperar que Docker Engine esté listo.
5. Verificar:

   ```powershell
   docker --version
   docker compose version
   docker info --format "{{.ServerVersion}}"
   ```

## 2. Preparar la carpeta (fuera del repo)

```powershell
mkdir C:\Users\ASUS\xiaozhi-server
cd C:\Users\ASUS\xiaozhi-server
mkdir data, models\SenseVoiceSmall
```

### 2.1 Descargar `docker-compose.yml` mínimo

Desde el repo oficial:

```powershell
curl.exe -L -o docker-compose.yml https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/main/main/xiaozhi-server/docker-compose.yml
```

Contenido esperado (resumido):

```yaml
version: '3'
services:
  xiaozhi-esp32-server:
    image: ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
    container_name: xiaozhi-esp32-server
    restart: always
    security_opt:
      - seccomp:unconfined
    environment:
      - TZ=America/Bogota
    ports:
      - "8000:8000"
      - "8003:8003"
    volumes:
      - ./data:/opt/xiaozhi-esp32-server/data
      - ./models/SenseVoiceSmall/model.pt:/opt/xiaozhi-esp32-server/models/SenseVoiceSmall/model.pt
```

> Alz: aunque el ASR final sea Whisper API (Groq/OpenAI), el compose **siempre** monta `model.pt`. Hay que colocar el archivo; no se puede omitir.

### 2.2 Descargar el modelo SenseVoiceSmall

El archivo pesa ~936 MB. Descargar solo `model.pt`:

```powershell
cd C:\Users\ASUS\xiaozhi-server\models\SenseVoiceSmall
curl.exe -L -o model.pt https://huggingface.co/FunAudioLLM/SenseVoiceSmall/resolve/13b56a3c83b4e4847b95d8f5134b4816b80245d7/model.pt
```

Alternativas: `harf download hf://FunAudioLLM/SenseVoiceSmall/model.pt` o descargar el modelo completo desde ModelScope (`iic/SenseVoiceSmall`).

## 3. Configuración mínima

Copiar la plantilla desde este prototipo:

```powershell
Copy-Item "G:\Mi unidad\Study\Universidad- Ing Sistemas\6 SEMESTRE\Desarrollo de Aplicaciones AV\Simulacion en Python\finagotchi\prototypes\xiaozhi\.config.yaml.example" C:\Users\ASUS\xiaozhi-server\data\.config.yaml
```

Editar `C:\Users\ASUS\xiaozhi-server\data\.config.yaml` (ver `CONFIG_XIAOZHI.md`): ASR = `GroqASR`, LLM = `GroqLLM` o `ChatGLMLLM`, TTS = `EdgeTTS` (primero) y luego `FinaGotchiTTS` (custom), Intent = `function_call`, prompt = plantilla Nancy.

> Nunca pondrás el `device_token` de FinaGotchi en este YAML: ese token vive solo en `prototypes/xiaozhi/config.local.json`.

## 4. Instalar la dependencia MCP del host (puente)

El pipe que corre en Windows necesita el paquete MCP (el contenedor trae el suyo):

```powershell
cd "G:\Mi unidad\Study\Universidad- Ing Sistemas\6 SEMESTRE\Desarrollo de Aplicaciones AV\Simulacion en Python\finagotchi\prototypes\xiaozhi"
py -3 -m pip install -r requirements.txt
```

## 5. Levantar el stack (orden exacto)

1. **Backend FinaGotchi** (ya corre en `5000`; si no, `py -3 backend/server.py`).
2. **Puente**:

   ```powershell
   py -3 prototypes/xiaozhi/bridge.py --host 127.0.0.1 --port 8787
   ```

3. **Xiaozhi**:

   ```powershell
   cd C:\Users\ASUS\xiaozhi-server
   docker compose up -d
   docker logs -f xiaozhi-esp32-server
   ```

   Copiar de los logs:
   - OTA: `http://<IP>:8003/xiaozhi/ota/`
   - Visión: `http://<IP>:8003/mcp/vision/explain`
   - **MCP endpoint:** `ws://<IP>:8004/mcp_endpoint/mcp/?token=...` (o el que indique el log; el puerto exacto depende de la versión)

4. **Pipe MCP** (en otra terminal):

   ```powershell
   $env:MCP_ENDPOINT = "ws://<IP>:8004/mcp_endpoint/mcp/?token=..."
   $env:XIAOZHI_BRIDGE_URL = "http://127.0.0.1:8787"
   cd "G:\...\prototypes\xiaozhi"
   py -3 mcp_servidor.py
   ```

## 6. Verificación rápida

- `docker logs -f xiaozhi-esp32-server` sin errores de módulos (`ASR`, `LLM`, `TTS`, `VAD`, `Intent`).
- En la PC: `http://127.0.0.1:8787/salud` → `"token_configurado": true`.
- Página de prueba del servidor (ver logs) o cliente software → hablar “gasté 20 mil en almuerzo” → debe llamar a `finagotchi_turno` → TTS dice “¿Registro un gasto de 20 mil pesos…?”.

## 7. Limpieza

```powershell
cd C:\Users\ASUS\xiaozhi-server
docker compose down
```

## 8. Alternativa sin Docker (Conda 3.10)

Solo si Docker no es viable:

```powershell
conda create -n xiaozhi-esp32-server python=3.10 -y
conda activate xiaozhi-esp32-server
conda install libopus ffmpeg -y
cd xiaozhi-esp32-server-main\main\xiaozhi-server
pip install -r requirements.txt
python app.py
```

> `torch==2.2.2` fijado: **requiere Python 3.10**. Tu Python 3.14 actual no sirve para esto.

## 9. Qué no se hace

- No se descarga ni modifica `xiaozhi-esp32-server` dentro del repo FinaGotchi.
- No se crea la cuenta en `xiaozhi.me` (nube oficial): con servidor propio no hace falta.
- No se sube ninguna clave a Git; todo queda en `C:\Users\ASUS\xiaozhi-server\data\.config.yaml` y `prototypes/xiaozhi/config.local.json` (ignorados).
