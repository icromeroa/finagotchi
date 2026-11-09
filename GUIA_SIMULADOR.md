# Simulador FinaGotchi (PC)

El simulador representa el dispositivo físico: inicia sesión con un usuario de prueba, vincula un dispositivo virtual, captura la voz, **envía el audio al backend** y pide la confirmación por voz.

**La voz es la entrada principal.** El menú solo informa de qué puedes decir y qué teclas existen; lo normal es hablar o escribir la misma frase. Quien no pueda hablar usa `[T] Escribir`. Con `[A] Probar micrófono` el simulador mide el pico y el RMS de la señal y explica por qué puedes no estar escuchando nada.

## Interfaz gráfica (GUI)

La forma principal de usar el simulador es la ventana moderna en `simulator/gui/` (CustomTkinter, paleta del mockup: fondo crema, marco verde, rosa y lima).

**Importante:** ejecuta el comando desde la **raíz del repositorio**, no desde dentro de `simulator/`. Si lo ejecutas dentro de esa carpeta, Python confunde `simulator.py` con el paquete y falla con `ModuleNotFoundError: No module named 'simulator.main'`.

```powershell
py -3 -m simulator.gui.app
```

En macOS (desde la raíz del proyecto):

```bash
python3 -m simulator.gui.app
```

Si tu terminal no tiene activado el entorno virtual del proyecto, usa directamente su Python:

```bash
.venv/bin/python -m simulator.gui.app
```

Qué muestra:

- **Cabecera** con fecha y hora y marco tipo dispositivo.
- **Nancy con sprite** (PNG/GIF según ánimo; el estado `escuchando`, `dormida` y las animaciones `ola`/`puntos` se muestran al grabar/procesar).
- **Tarjetas estructuradas**, nunca diccionarios crudos:
  - *Cuentas*: rejilla con distintivo PREDET./TUYA, nº de movimientos y saldo.
  - *Categorías*: pestañas Gastos/Ingresos con nº de movimientos por categoría.
  - *Metas*: total ahorrado, barra de progreso y detalle por meta (monto, %, fecha, aporte).
  - *Pendientes* y *movimientos*: lista con tipo, monto, categoría/cuenta y fecha.
- **Botones Sí/No** cuando Nancy pide confirmación (hablan la misma frase por el flujo conversacional).
- **Entrada dual**: campo de texto y botón **Hablar** (clic para empezar a grabar, clic en **Detener** para terminar) + acciones Estado, Plan, Cerrar, Avisos, Repetir, Voz y Salir.

**Nancy lo dice en voz, no lo muestra**: la frase larga de Nancy no se pinta en la GUI (se reproduce por Piper o el banco offline). Solo los avisos (aclaración/error/ayuda) se muestran como tarjeta, porque sin ellos no sabrías por qué se pidió aclaración.

Sprites e imágenes en `simulator/gui/assets/` (`sprites/`, `gifs/`, `iconos/`): ver `simulator/gui/assets/README.md` para los nombres exactos (`nancy_feliz.png`, `nancy_preocupada.png`, `nancy_escuchando.gif`, …). Si falta un archivo, la GUI dibuja un placeholder rosa y nunca se rompe. Las fuentes Outfit/Space Grotesk están en `simulator/gui/fonts/`.

La consola (`py -3 simulator/main.py`) sigue disponible como alternativa sin ventana y se comporta igual.

Recorre las mismas pantallas que tendrá el firmware, definidas en `docs/DISPOSITIVO.md`:

| Pantalla | Qué muestra |
|---|---|
| D03 Reposo | Fecha y hora (p. ej. `sáb 7 nov · 22:55`), ánimo de Nancy, salud, cupo del día, gastos, ingresos, puntos, conexión y batería. |
| D04 Grabando | "Te escucho", el tiempo transcurrido y la barra de audio. |
| D05 Procesando | "Entendiendo tu mensaje". |
| D06 Confirmar | "¿Registro esto?" con tipo, monto, categoría, cuenta y la frase transcrita. |
| D07 Resultado | "Listo", los puntos ganados y el cupo restante. |
| D08 Consulta | "Así vas hoy": ingresos, gastos, ahorro, balance, cupo, salud y ánimo. |
| D09 Cierre | El resumen del cierre del día. |
| D10 Sin conexión | "No pude enviar tu mensaje. Voy a intentarlo otra vez". |
| D11 No entendí | Pide repetir con el monto y el tipo de movimiento. |
| D13 Avisos | Las notificaciones del dispositivo. |
| D14 Plan de ahorro | El plan LP de metas, solo lectura. |
| D15 Respuesta de Nancy | Lo que Nancy dijo (voz y texto comparten pantalla). En la GUI el texto largo no se pinta: solo se reproduce en voz y en pantalla va la tarjeta estructurada. |
| D16 Error explicado | El motivo del error y la alternativa. |
| D17 Prueba de micrófono | Pico y RMS de la señal y si hay voz. |

## Menú

```
  Habla con Nancy o escribe la misma frase natural.
  Puedes decir:
   - Gasté 20 mil en almuerzo
   - Ahorré 50 mil para mi meta
   - Quiero crear una meta para comprar audífonos
   - ¿Cómo me fue hoy?  /  ¿Cómo van mis metas?
   - Sí, está bien  /  No, cancela

  [H] Hablar   [T] Escribir   [A] Probar micrófono
  [E] Estado del día   [C] Cerrar el día
  [P] Plan de ahorro   [N] Notificaciones
  [R] Repetir la última frase   [S] Salir
```

Presionar `Enter` en el menú equivale a `[H] Hablar`; cualquier frase natural
escrita se envía directamente al agente, como si la hubieras dicho.

Cuando Nancy pide confirmación tras una frase hablada, el micrófono vuelve a
escuchar automáticamente sin pasar por el menú; si entraste por `[T]`, el
simulador te recuerda usar `[H]` o `[T]` para responder.

## Sobre la transcripción y la IA

El simulador no transcribe en el PC. Graba un WAV de 16 kHz mono y lo sube por `multipart/form-data` a `POST /api/v1/device/messages`. La transcripción la hace `faster-whisper` o faster-whisper en el backend, y la interpretación de la frase (tipo, monto, categoría y cuenta) la hace un modelo de lenguaje con Ollama. Es exactamente el camino que seguirá el firmware de la ESP32.

## Voz de Nancy

Con `[V]` activas o silencian la voz. El flujo es:

1. La respuesta dice `"voz": {"endpoint": "/api/v1/device/voice/synthesize"}` si el backend tiene Piper disponible.
2. El simulador pide la WAV directamente al endpoint; la WAV se genera en memoria y no se guarda.
3. Si el backend no tiene Piper, reproduce frases cortas pregrabadas cuando la respuesta es predecible.
4. Las respuestas largas se muestran como texto; no se leen completas por el banco offline.

Para instalar la voz local (fuera del repositorio; no se versiona el modelo):

```bash
# macOS / Linux
.venv/bin/python tools/configurar_voz.py

# Windows
py -3 tools/configurar_voz.py
```

Por defecto instala `es_MX-claude-high.onnx` en `~/.finagotchi/piper`
(`%USERPROFILE%\.finagotchi\piper` en Windows). En macOS la reproducción usa
`sounddevice`, no `winsound`; si no hay altavoz o modelo, el simulador sigue
mostrando el texto sin bloquear. Comprueba el estado con:

```bash
.venv/bin/python -c "from backend import tts; print(tts.disponible(), tts.model_path())"
```

## Requisitos

- Python 3.10 o superior.
- Micrófono.
- Conexión a Internet **opcional**: con Ollama (`qwen3:4b`) y faster-whisper el flujo completo funciona offline.
- En macOS, solo la consola usa `keyboard` (requiere `sudo`); la GUI graba por clic y **no** necesita permisos de administrador.

## Instalación

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m pip install -r requirements-simulator.txt
```

No se necesita clave de API. Solo verifica que el modelo local esté instalado:

```powershell
py -3 tools/verificar_entorno.py
```

Sin faster-whisper, el backend responde `STT_NO_CONFIGURADO` cuando llega audio.

> No copies un secreto a `backend/.env.example` (está versionado en git).

### Si la transcripción local no funciona

El backend transcribe siempre con `faster-whisper` local (sin clave, sin cuota y sin internet). Para activarlo:

```powershell
py -3 -m pip install faster-whisper
```

El simulador muestra con qué proveedor se transcribió:

```
[TRANSCRIPTO POR]: local whisper-base
```

El modelo se elige con `STT_MODELO_LOCAL` (`tiny`, `base`, `small`, `medium`, `large-v3`; por defecto `base`) en `backend/.env`.

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
  "http_base_url": "http://127.0.0.1:5001/api/v1",
  "device_uid": "FINAGOTCHI-PC-SIMULATOR-01",
  "email": "simulador@finagotchi.local",
  "password": "simulador123",
  "nombre": "Simulador",
  "input_device": null,
  "voice_output": true,
  "voice_scope": "resumen",
  "sample_rate": 16000,
  "language": "es-CO",
  "stt_provider": "local",
  "request_timeout_s": 90
}
```

- `input_device`: escribe el índice del micrófono que quieres usar (`py -3 simulator/main.py` y opción `[A]`); en `null` usa el predeterminado.
- `voice_output`: activa/desactiva que Nancy hable.
- `voice_scope`: qué respuestas habla Nancy. `resumen` (recomendado) habla confirmaciones, resultados, consultas, aclaraciones y errores con el `texto_voz` corto, y deja el detalle en pantalla; `acciones` limita la voz a confirmaciones y resultados; `todo` también lee las consultas completas. El audio se genera en memoria y nunca se guarda.
- `request_timeout_s` sube a 90 porque la transcripción y la IA pueden tardar varios segundos (faster-whisper 3–6 s, Ollama 2–25 s según el equipo).
- Si el usuario no existe, el simulador lo registra automáticamente.
- Si el dispositivo ya está vinculado a esa cuenta, lo desvincula y lo vuelve a vincular.

## Ejecución

Terminal 1, desde la raíz del proyecto:

```powershell
py -3 backend/server.py
```

Terminal 2, ejecutada como administrador (GUI moderna):

```powershell
py -3 -m simulator.gui.app
```

O la consola clásica:

```powershell
py -3 simulator/main.py
```

### En macOS (MacBook): pasos y cambio de puerto

En Windows se usa `py -3`; en Mac se usa `python3`. El flujo es el mismo.

1. **Instalar dependencias** (desde la raíz del repositorio, en cualquier terminal):

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-simulator.txt
python3 tools/verificar_entorno.py
```

> Desde Python 3.10 en adelante (`python3 --version`). Si `faster-whisper` no está, instálalo con:
> `python3 -m pip install faster-whisper`

2. **Levantar el backend en puerto 5001** (otra Terminal, deja esta ventana abierta):

```bash
PORT=5001 python3 backend/server.py
```

Sin `PORT=`, el backend escucha en 5000.

3. **Apuntar el simulador a ese puerto** — edita `simulator/config.json`:

```json
{
  "http_base_url": "http://127.0.0.1:5001/api/v1"
}
```

También puedes usar la variable de entorno `FINAGOTCHI_BASE_URL`.

4. **Verificar la conexión (otra Terminal, dejarla abierta):**

```bash
curl http://localhost:5001/api/v1/health
```

Debe responder `{"ok": true, "data": {"estado": "ok", …}}`. Si no responde, el backend no está en 5001: revisa que lo levantaste con `PORT=5001`, que la terminal del backend sigue abierta y que no haya firewall bloqueando el puerto.

5. **Levantar el simulador** (Mac):

```bash
python3 simulator/main.py
```

O la GUI (macOS puede pedir permiso especial), también **desde la raíz del repositorio**:

```bash
python3 -m simulator.gui.app
```

Si `python3` no tiene `customtkinter`, usa el Python del entorno virtual:

```bash
.venv/bin/python -m simulator.gui.app
```

> **Micrófono en macOS:** la GUI no usa la tecla ESPACIO: pulsa **Hablar** para empezar a grabar y **Detener** para terminar (no hace falta `sudo`). La consola sí usa `keyboard`, que en macOS exige `sudo`; si no lo tienes, cae automáticamente a **ENTER**.

**Error típico “No se pudo conectar con el backend”:** casi siempre es “levanté el backend en 5000 pero el simulador busca 5001” (o al revés). Todo debe coincidir: **mismo puerto, backend abierto y simulador apuntando a ese puerto**.

Elige `[H] Hablar` y mantén presionada la tecla ESPACIO mientras hablas. Al soltarla, el simulador envía el WAV al backend, muestra la transcripción, propone los movimientos o la acción, y te pide que respondas con una frase natural:

- "sí", "ok", "correcto", "está bien", "confirmo" → confirmar.
- "no", "cancela", "olvídalo", "descarta" → descartar.
- "cambia el monto a 25 mil" → corregir antes de confirmar.

Si la voz está activada, Nancy la pronuncia en voz alta; usa `[V]` para alternar.

Si no puedes hablar, usa `[T] Escribir` o escribe la misma frase en el menú. Con `[A] Probar micrófono` verificas que llegue señal antes de culpar al STT.

> **El archivo de entrada se llama `main.py` y no `simulator.py` a propósito.** Si el módulo se llamara igual que el paquete, al ejecutarlo directamente Python lo cargaría como `simulator` y el import de las pantallas fallaría con `ImportError: cannot import name 'pantallas' from 'simulator'`. El atajo `simulator/simulator.py` se conserva para que el comando viejo siga sirviendo.
>
> Si el hook de teclado no está disponible (en Windows suele hacer falta ejecutar como administrador), el simulador **no se cae**: avisa que usará la tecla ENTER, donde una pulsación empieza a grabar y la siguiente la detiene.
>
> Si el backend no está levantado, el simulador **no se cae**: dice que no pudo conectarse y muestra el comando exacto para levantarlo.
>
> `tests/test_comandos.py` ejecuta estos comandos de verdad, para que un comando documentado nunca vuelva a fallar sin avisar.

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

- "¿Cómo me fue hoy?"
- "Balance de esta semana" (lunes a hoy)
- "Balance del mes"
- "¿Cuánto gasté ayer?"
- "Gasté ayer" (sin monto: consulta con total hablado y lista en pantalla)
- "Movimientos de ayer"
- "Gastos del 3 al 5 de mayo"
- "¿Cómo van mis metas?"
- "¿Qué tengo pendiente?" (movimientos sin confirmar; no los resuelve)
- "¿Cuáles son mis cuentas?" (base vs. propias, sin ocultas, con saldo)
- "¿Cuáles son mis categorías de gasto?" (nº de registros y total por categoría)
- "Cierra el día"

Fechas al registrar:

- "Gasté 20 mil en almuerzo ayer" → propone el gasto con fecha de ayer y pide confirmación.
- "Gasté 15 mil en comida el 3 de mayo" → registra ese día si está dentro de los últimos 365 días.
- Una fecha futura se rechaza con una aclaración y no crea el pendiente.

Metas por voz:

- "Quiero crear una meta para comprar unos audífonos"
- "Quinientos mil" · "en cinco meses" · "mensual" · "prioridad alta"
- "Sí" → confirma y la meta se crea (solo entonces)

Otras operaciones:

- "Crea una cuenta llamada Ahorros de tipo cuenta de ahorros"
- "Crea una categoría llamada Mascotas de gasto"
- "Agrega esta categoría Belleza en gasto"
- "Agrega la subcategoría Accesorios de ingreso"
- "Gasté 10 mil en accesorios" (si no existe, Nancy pregunta si la crea)
- "Cambia mi presupuesto diario a 30 mil"
- "Mi ingreso mensual es 2 millones"
- "Elimina la meta Viaje"
- "Elimina el último movimiento"
- "Edita el último movimiento"

Correcciones del pendiente:

- "No está bien, la cuenta es Nequi"
- "No es de ayer, es de hoy"
- "Con la categoría de Belleza" (si no existe, ofrece crearla y aplicarla)

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

El simulador envía el archivo `audio` (o el texto), `message_id`, `duracion_audio_s` e `idioma`. El backend valida el WAV, lo transcribe, registra la auditoría en `interacciones_ia` y crea las transacciones en estado `pendiente`. Solo la confirmación — por voz, por texto o por endpoint — las vuelve `confirmado`, otorga puntos y afecta el saldo. El audio nunca se guarda.

El `message_id` se genera una vez por grabación, así que un reintento no duplica el registro. Con `NLP_USAR_IA=off` en el entorno del backend, el intérprete usa solo las reglas y no llama a ningún LLM.

## Problemas frecuentes

- `ERROR DE CONEXIÓN`: verifica que el backend escuche en `http://127.0.0.1:5001`.
- `401` o `403`: el dispositivo está vinculado a otra cuenta; usa otro `device_uid` o desvincula el dispositivo desde la app.
- `keyboard` no detecta ESPACIO: ejecuta la terminal como administrador.
- `503 STT_NO_CONFIGURADO`: falta la clave de faster-whisper (o usa `LLM_PROVEEDOR`/`STT_PROVEEDOR` locales que no la necesita).
- `422 AUDIO_INVALIDO`: el audio no es WAV de 16 kHz mono, o está fuera del rango de 0,5 a 40 segundos.
- `502 STT_NO_DISPONIBLE`: faster-whisper no respondió. El simulador reintenta con el mismo `message_id`.
- `429 STT_CUOTA`: se alcanzó la cuota de la capa gratuita; esperar y reintentar.
- El simulador dice "No escuché tu voz" o la estadística de pico es 0: el micrófono está silenciado, mute o con índice equivocado. Usa `[A] Probar micrófono` y ajusta `input_device` en `simulator/config.json`.
- El backend no arranca: verifica `py -3 database/init_db.py` y que `finagotchi.db` no sea una base legacy.

