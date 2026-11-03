# Simulador FinaGotchi (PC)

El simulador representa el dispositivo físico: inicia sesión con un usuario de prueba, vincula un dispositivo virtual, captura la voz, **envía el audio al backend** y confirma el registro propuesto.

Recorre las mismas pantallas que tendrá el firmware, definidas en `docs/DISPOSITIVO.md`:

| Pantalla | Qué muestra |
|---|---|
| D03 Reposo | Ánimo de Nancy, salud, cupo del día, gastos, ingresos, puntos, conexión y batería. |
| D04 Grabando | "Te escucho", el tiempo transcurrido y la barra de audio. |
| D05 Procesando | "Entendiendo tu mensaje". |
| D06 Confirmar | "¿Registro esto?" con tipo, monto, categoría, cuenta y la frase transcrita. |
| D07 Resultado | "Listo", los puntos ganados y el cupo restante. |
| D08 Consulta | "Así vas hoy": ingresos, gastos, ahorro, balance, cupo, salud y ánimo. |
| D09 Cierre | El resumen del cierre del día. |
| D10 Sin conexión | "No pude enviar tu mensaje. Voy a intentarlo otra vez". |
| D11 No entendí | Pide repetir con el monto y el tipo de movimiento. |
| D13 Avisos | Las notificaciones del dispositivo. |

## Menú

```
  [H] Hablar   [E] Estado del dia   [C] Cerrar el dia
  [N] Notificaciones   [R] Repetir la ultima frase   [S] Salir
```

## Sobre la transcripción y la IA

El simulador no transcribe en el PC. Graba un WAV de 16 kHz mono y lo sube por `multipart/form-data` a `POST /api/v1/device/messages`. La transcripción la hace `faster-whisper` o Gemini en el backend, y la interpretación de la frase (tipo, monto, categoría y cuenta) la hace un modelo de lenguaje con Ollama. Es exactamente el camino que seguirá el firmware de la ESP32.

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

### Si la clave de Gemini no funciona

Google está cambiando el formato de sus claves: desde el 28 de mayo de 2026 AI Studio solo emite "Auth keys" (`AQ.Ab...`) y hay un problema abierto por el que devuelven `401 ACCESS_TOKEN_TYPE_UNSUPPORTED`.

El simulador funciona igual gracias al **proveedor local**: `faster-whisper` corriendo en tu PC, sin clave, sin cuota y sin internet. Para activarlo:

```powershell
py -3 -m pip install faster-whisper
```

Con `STT_PROVEEDOR=auto` (el valor por defecto) no hay que hacer nada: el backend intenta Gemini y cae al modelo local si la clave falla. El simulador muestra con qué proveedor se transcribió:

```
[TRANSCRIPTO POR]: local whisper-base
```

Para forzar siempre el modelo local, pon `STT_PROVEEDOR=local` en `%USERPROFILE%\.finagotchi\gemini.env`.

### El modelo que interpreta la frase

Transcribir no es suficiente: hace falta un modelo que entienda **qué tipo de movimiento es, el monto, la categoría y la cuenta**. Eso lo hace un modelo de lenguaje local con **Ollama**:

```powershell
winget install --id Ollama.Ollama --exact --silent
ollama pull qwen3:4b
```

Es gratis, corre en tu PC, no necesita clave ni internet. El backend recibe el catálogo real del usuario (sus 16 categorías y sus 5 cuentas) y el modelo responde un JSON que después se valida contra la base de datos: si inventa una categoría que no existe, se descarta.

Ejemplo de lo que entiende:

| Dices | Transcripción | Tipo | Monto | Categoría | Cuenta |
|---|---|---|---|---|---|
| "gasté 20.000 por nequi" | "Gasté 20.000 pesos por Nequi." | gasto | $20.000 | Otros | **Nequi** |
| "compré 5.000 con daviplata en el almacén" | "Compré 5.000 con Daviplata en el almacén." | gasto | $5.000 | **Alimentación** | **Daviplata** |
| "me pagaron 800.000 a la cuenta nu" | "Me pagaron 800.000 a la cuenta Nu." | ingreso | $800.000 | **Trabajo** | **Nu** |

Ojo: la transcripción sola escribía "por **Nike**" y "con **David Plata**". Para evitarlo, el backend manda los nombres de tus cuentas y categorías al modelo de transcripción como pistas (hotwords).

Si Ollama no está instalado, el backend cae a las reglas por palabra clave y todo sigue funcionando, pero la categoría y la cuenta se detectan con menos precisión.

Para ver qué está activo:

```powershell
py -3 tools/verificar_entorno.py
```

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
py -3 simulator/main.py
```

Elige `[H] Hablar` y mantén presionada la tecla ESPACIO mientras hablas. Al soltarla, el simulador envía el WAV al backend, muestra la transcripción, propone los movimientos, pide la confirmación y muestra el resultado.

> El archivo se llama `main.py` y no `simulator.py` a propósito. Si el módulo se llamara igual que el paquete, al ejecutarlo directamente Python lo cargaría como `simulator` y el import de las pantallas fallaría con `ImportError: cannot import name 'pantallas' from 'simulator'`. El paquete `simulator/` tiene su `__init__.py` y se puede importar igual desde el código: `from simulator import pantallas`.
>
> Hay una prueba que ejecuta exactamente estos dos comandos (`tests/test_comandos.py`), para que un comando documentado nunca vuelva a fallar sin avisar.

> El servidor ya no reinicia solo cuando cambias un archivo. Con el reinicio automático de Flask, cualquier cambio en el proyecto cortaba las peticiones en vuelo y el audio se perdía a medio enviar. Para depurar con recarga automática: `FLASK_DEBUG=1 py -3 backend/server.py`.

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

El simulador envía el archivo `audio`, `message_id`, `audio_duracion_s` e `idioma`. El backend valida el WAV, lo transcribe, registra la auditoría en `interacciones_ia` y crea las transacciones en estado `pendiente`. Solo la confirmación las vuelve `confirmado`, otorga puntos y afecta el saldo. El audio nunca se guarda.

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
