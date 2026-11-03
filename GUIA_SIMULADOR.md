# Simulador FinaGotchi (PC)

El simulador representa el dispositivo físico: inicia sesión con un usuario de prueba, vincula un dispositivo virtual, captura la voz, **envía el audio al backend** y confirma el registro propuesto.

> El simulador ya no transcribe en el PC. Graba un WAV de 16 kHz mono y lo sube por `multipart/form-data` a `POST /api/v1/device/messages`. La transcripción la hace Gemini Flash en el backend y la clasificación por reglas, exactamente como será en el firmware de la ESP32.

## Requisitos

- Python 3.10 o superior.
- Micrófono.
- Conexión a Internet (el backend llama a la API de Gemini).
- Backend con la API key configurada en `backend/.env`.
- Permisos de administrador para que `keyboard` capture la tecla ESPACIO.

## Instalación

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m pip install -r requirements-simulator.txt
```

El backend necesita la clave de Gemini. La clave se guarda **fuera del repositorio**, en `%USERPROFILE%\.finagotchi\gemini.env`:

```powershell
py -3 tools/configurar_api_key.py
```

El asistente pide la clave, la guarda en ese archivo y la verifica contra la API. Para ver el estado:

```powershell
py -3 tools/verificar_entorno.py
```

Sin clave, el backend responde `STT_NO_CONFIGURADO` cuando llega audio.

> No copies la clave a `backend/.env.example`: ese archivo está versionado en git.

## Configuración

Edita `simulator/config.json`:

```json
{
  "http_base_url": "http://127.0.0.1:5000/api/v1",
  "device_uid": "FINAGOTCHI-PC-SIMULATOR-01",
  "email": "simulador@finagotchi.local",
  "password": "simulador123",
  "nombre": "Simulador",
  "auto_confirm": true,
  "sample_rate": 16000,
  "language": "es-CO",
  "stt_provider": "gemini",
  "request_timeout_s": 90
}
```

- `auto_confirm: true` guarda las propuestas sin pedir confirmación.
- `auto_confirm: false` muestra la propuesta y pide `[S/n]`.
- `request_timeout_s` sube a 90 porque la transcripción puede tardar entre 3 y 6 segundos.
- Si el usuario no existe, el simulador lo registra automáticamente.
- Si el dispositivo ya está vinculado a esa cuenta, lo desvincula y lo vuelve a vincular.

## Ejecución

Terminal 1, desde la raíz del proyecto:

```powershell
py -3 backend/server.py
```

Terminal 2, ejecutada como administrador:

```powershell
py -3 simulator/simulator.py
```

Mantén presionada la tecla ESPACIO mientras hablas. Al soltarla, el simulador envía el WAV al backend, muestra la transcripción que devuelve Gemini, propone los movimientos, confirma y consulta las notificaciones.

## Frases de prueba

Gastos:

- "Gasté 12.000 en el almuerzo"
- "Pagué 8.000 de transporte"
- "Compré un café por 5 mil"
- "Gasté catorce mil en el almuerzo"

Ingresos:

- "Me pagaron 50.000 por un trabajo"
- "Recibí 20.000 de mesada"
- "Me pagaron dos millones del trabajo"

Ahorro:

- "Ahorré 30.000 para el portátil"

Consultas y cierre:

- "¿Cómo voy hoy?"
- "Dame mi balance"
- "Cierra el día"

## Flujo técnico

1. `POST /auth/login`; si falla, `POST /auth/register`.
2. `POST /device/register` para obtener un PIN.
3. `POST /device/pair` para obtener `device_token`.
4. `POST /device/telemetry` como latido.
5. `POST /device/messages` con el WAV en `multipart/form-data` y `message_id`.
6. Si hay una propuesta, `POST /device/messages/{id}/confirm`.
7. Tras confirmar, `GET /device/notifications?after_id=N` y `POST /device/notifications/{id}/ack`.
8. Para cierre, `POST /device/close-day`.
9. Para consultas, `GET /home`.

El simulador envía el archivo `audio`, `message_id`, `audio_duracion_s` e `idioma`. El backend valida el WAV, lo transcribe con Gemini, registra la auditoría en `interacciones_ia` y crea las transacciones en estado `pendiente`. Solo la confirmación las vuelve `confirmado`, otorga puntos y afecta el saldo. El audio nunca se guarda.

El `message_id` se genera una vez por grabación, así que un reintento no duplica el registro.

## Problemas frecuentes

- `ERROR DE CONEXIÓN`: verifica que el backend escuche en `http://127.0.0.1:5000`.
- `401` o `403`: el dispositivo está vinculado a otra cuenta; usa otro `device_uid` o desvincula el dispositivo desde la app.
- `keyboard` no detecta ESPACIO: ejecuta la terminal como administrador.
- `503 STT_NO_CONFIGURADO`: falta `GEMINI_API_KEY` en `backend/.env`.
- `422 AUDIO_INVALIDO`: el audio no es WAV de 16 kHz mono, o está fuera del rango de 0,5 a 40 segundos.
- `502 STT_NO_DISPONIBLE`: Gemini no respondió. El simulador reintenta con el mismo `message_id`.
- `429 STT_CUOTA`: se alcanzó la cuota de la capa gratuita; esperar y reintentar.
- El backend no arranca: verifica `py -3 database/init_db.py` y que `finagotchi.db` no sea una base legacy.
