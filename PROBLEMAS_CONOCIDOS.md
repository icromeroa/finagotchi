# Problemas conocidos

Registro de los errores encontrados durante el desarrollo, como se resolvieron y los que siguen abiertos.

Estado al cierre de la Fase A y la fase del simulador por menús.

## Errores encontrados y resueltos

### El simulador no arrancaba

| Síntoma | Causa | Resolución |
|---|---|---|
| `ImportError: cannot import name 'pantallas' from 'simulator'` al ejecutar `py -3 simulator/simulator.py` | El archivo de entrada se llamaba igual que el paquete que lo contenía. Al ejecutarlo directamente, Python pone el directorio del script primero en `sys.path`, encuentra `simulator.py` y lo carga como el módulo `simulator`, que no tiene el atributo `pantallas`. | La entrada pasó a `simulator/main.py` y el paquete tiene `__init__.py`. Se dejó además `simulator/simulator.py` como atajo para que el comando viejo siga funcionando. |
| La falla no la detectaban las pruebas | El módulo se probaba importándolo, que sí funciona. La falla solo aparece al ejecutar el comando. | Se agregó `tests/test_comandos.py`: levanta el backend en un puerto libre y ejecuta los comandos documentados. |
| `ConnectionResetError` al enviar el audio | El servidor de Flask arrancaba con `debug=True`, que activa el reinicio automático. Cualquier cambio de archivo reiniciaba el proceso y cortaba la petición en vuelo. | El reinicio automático quedó desactivado por defecto. Se activa con `FLASK_DEBUG=1`. |
| `UnicodeEncodeError: 'charmap' codec` al imprimir las pantallas | La consola de Windows usa cp1252 y no puede imprimir los caracteres de cuadro de las líneas. | Las pantallas se dibujan con caracteres ASCII. |
| El simulador no mostraba los ingresos del día | La API siempre devolvió ingresos, gastos, ahorro y balance. El bug estaba en el simulador, que solo pintaba gastos y cupo. | La pantalla D08 "Así vas hoy" muestra el balance completo. |
| El backend respondía con la página de depuración de HTML en vez de JSON | No había manejador para errores inesperados. | Se agregó un manejador que responde JSON en el error 500. |
| `CHECK constraint failed` al guardar una transacción | El esquema exige categoría en todo movimiento distinto de ahorro, y la interpretación por IA podía devolverla nula. | Todo movimiento recibe la categoría de último recurso ("Otros" u "Otros ingresos"). |

### La API key de Gemini

| Síntoma | Causa | Resolución |
|---|---|---|
| `503 STT_NO_CONFIGURADO` con la clave puesta | El archivo `backend/.env` se había borrado. | La clave se guarda ahora fuera del repositorio, en `%USERPROFILE%/.finagotchi/gemini.env`, con `tools/configurar_api_key.py`. |
| `401 UNAUTHENTICATED` / `ACCESS_TOKEN_TYPE_UNSUPPORTED` | La clave empezaba con `AQ.Ab` (Auth key). Desde el 28 de mayo de 2026 AI Studio solo emite Auth keys y hay un problema abierto de compatibilidad con `generativelanguage.googleapis.com`. No es un error del código. | Se agregó el proveedor local de transcripción (faster-whisper) que no necesita clave, ni cuota ni internet, y `STT_PROVEEDOR=auto` cae a él automáticamente. |
| La clave podía quedar versionada | `backend/.env.example` sí está versionado en git. | `tests/test_seguridad.py` falla si una clave con formato de Google aparece en cualquier archivo del repo, y se limpió el archivo. |

### La transcripción y la IA

| Síntoma | Causa | Resolución |
|---|---|---|
| "gasté por nequi" no detectaba la cuenta | El modelo de ASR escribe las marcas de forma aproximada: "por Nike", "con David Plata", "a la cuenta no". | El backend manda los nombres de las cuentas y categorías del usuario como *hotwords* al modelo de transcripción. |
| La categoría y la cuenta no se asignaban bien | Las reglas por palabra clave no alcanzan para decidir el contexto ("en el almacén" no está en ninguna lista). | Se agregó la interpretación con modelo de lenguaje (Ollama con `qwen3:4b`), con validación de la respuesta contra el catálogo real del usuario. |
| La transcripción tardaba 38 segundos | Qwen3 viene con "modo pensar" activado. | La llamada a Ollama usa `think: false`. La misma llamada bajó a 2,6 segundos. |
| `qwen3:1.7b` clasifica mal | Es más rápido (4,5 s) pero dice que un almuerzo es Transporte y que ahorrar es un ingreso. | Se usa `qwen3:4b` por defecto: 4 de 4 frases correctas con 7,2 segundos. |
| Las categorías del usuario no se respetaban | La IA podía inventar una categoría que no existe. | La respuesta se valida contra la base: lo que no existe se descarta y se usa el valor por defecto. |

### Los montos

| Síntoma | Causa | Resolución |
|---|---|---|
| "catorce mil" no se entendía | El intérprete solo tenía una lista fija de frases en palabras. | Se reescribió el intérprete: entiende cifras y palabras, de "catorce mil" a "dos millones quinientos mil". |
| Los millones no se detectaban | El patrón no contemplaba "millones". | Se reconoce "millones" y "1.5 millones". |
| "5 mil" se perdía | El modelo de transcripción lo escribe "5.000". | El intérprete entiende las dos formas. |

## Errores abiertos

| Problema | Impacto | Plan |
|---|---|---|
| El mensaje con dos transacciones solo genera una | Se pierde parte de la información | El esquema ya soporta varias transacciones por mensaje; falta la segmentación en `backend/nlp.py`. |
| La app en Chrome no podía iniciar sesión aunque el backend estuviera bien | **Error de CORS por "red privada".** Desde Chrome 115, una página web que pide datos a un servidor de la red local envía `Access-Control-Request-Private-Network: true` en el preflight. El backend no respondía con `Access-Control-Allow-Private-Network: true`, así que **el navegador bloqueaba la petición y nunca llegaba al servidor**. | El backend responde ahora ese permiso cuando el navegador lo pide, con `tests/test_cors.py` como prueba. |
| La app no dejaba llegar al home sin vincular el dispositivo | El paso de enlace era obligatorio | Se agregó el botón "Ahora no" en `device_link_screen.dart`, que lleva directo al home. |
| La app Flutter no tiene capa HTTP | El frontend no consumía la API | **Resuelto en la fase B:** `frontend/lib/api/` con el cliente HTTP, la pantalla de acceso y la pantalla principal ya hablan con el backend. Falta conectar el onboarding (15 pantallas). |
| En web no se puede grabar la voz | El navegador solo ofrece webm/opus y el backend acepta WAV | La app lo detecta y ofrece escribir la frase a mano. La voz funciona en Android e iOS. |
| Flutter 3.47.9 está en `C:\Users\ASUS\Downloads\flutter` pero no en el PATH de las terminales abiertas | Flutter no se encuentra | Cerrar y abrir la terminal, o usar `C:\Users\ASUS\Downloads\flutter\bin\flutter.bat` |
| La carpeta `frontend/assets/animations/` no existía | `flutter test` y `flutter build` fallaban al leer el pubspec | Se creó la carpeta con su `.gitkeep`. |
| Flutter no está en el PATH de las terminales abiertas | Flutter 3.47.9 está instalado en `C:\Users\ASUS\Downloads\flutter`, pero las terminales abiertas antes de la instalación no lo ven | Cerrar y abrir la terminal, o usar la ruta completa: `C:\Users\ASUS\Downloads\flutter\bin\flutter.bat` |
| La base de datos es versionada en git | Cada cambio de esquema aparece en el diff | Dejarla así durante el desarrollo; sacarla del índice antes de publicar. |
| El dataset de 500 casos es sintético | No hay línea base con voz humana | `tools/grabar_dataset.py` graba los clips con el micrófono y `tools/evaluar_dataset.py` mide el WER, los montos y la latencia. |
| `flutter test` intercepta las peticiones HTTP | Las pruebas contra el backend real fallaban con "respuesta que no se pudo leer" | En `frontend/test/api_client_test.dart` se anula `HttpOverrides.global` para que las peticiones salgan de verdad. |
| El endpoint `/metrics/diagnosis` de la documentación no existe | El backend expone `/metrics/diagnostics` | Corregir la documentación en la fase B. |
| Endpoints de app documentados pero no implementados | `/notifications`, `/notification-preferences`, `/trash`, `/transactions/bulk-confirm`, `/device/commands` | Fase B: implementarlos o retirarlos de la documentación. |
| No existe firmware de la ESP32 | El dispositivo físico no funciona | Fase D: grabación I2S, envío por Wi-Fi, polling de notificaciones y pantalla. |
| La ESP32 no puede guardar 40 s de WAV en SRAM | Límite físico de 512 KB | Streaming por Wi-Fi o cola temporal en flash. Decisión de firmware pendiente. |
| El modelo de IA vive en el PC del desarrollador | Solo funciona en la red local | Hoy el backend corre en el PC y la ESP32 apunta a su IP. Cuando pase a un servidor solo cambia la URL: el firmware no cambia. |
| BLE sin implementar | Solo configuración | El MVP usa Wi-Fi; BLE queda para la vinculación inicial. |
| `qwen3:4b` tarda 7 segundos en interpretar | La espera después de hablar | Se puede bajar a `qwen3:1.7b` con `OLLAMA_MODEL`, pero clasifica peor. Aceptable: la pantalla D05 muestra "Entendiendo tu mensaje". |
