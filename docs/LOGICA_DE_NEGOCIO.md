# FinaGotchi · Lógica de negocio implementada

Documento técnico de la lógica que **hoy ejecuta el código**, no de la que
idealmente debería existir.

| Dato | Valor |
|---|---|
| Versión del documento | 1.2 |
| Fecha de corte | 2026-11-05 |
| Rama de referencia | `michelle` |
| Commits revisados | `e5290f5` (Fase 11) y `a554b68` (Fase 12 parcial) |
| Base de datos | SQLite, esquema 4 |
| Moneda | peso colombiano (COP), enteros |
| Zona horaria usada por el backend | `America/Bogota` (UTC-5) |

## 0. Cómo leer este documento

### 0.1 Fuente de verdad

La fuente de verdad es el código de `backend/`, `database/` y `simulator/`.
`docs/ESPECIFICACIONES.md` describe el contrato funcional deseado; cuando
diverge del código, este documento señala la diferencia. Las referencias son
por archivo y función, no por número de línea, para que no envejezcan con cada
edición.

Etiquetas usadas:

- **Implementado**: hay código que lo ejecuta y una ruta o una prueba que lo
  ejercita.
- **Modelado sin uso**: existe una tabla, columna o constante, pero ningún
  flujo real la utiliza.
- **Especificado sin implementar**: aparece en la especificación o en la
  documentación, pero no existe en el backend actual.

### 0.2 Resumen ejecutivo

FinaGotchi es, en la práctica, un **backend Flask + SQLite**. El backend hace
todo el trabajo de negocio: autentica, interpreta frases, crea propuestas de
movimiento, exige confirmación, calcula presupuestos, puntos, metas, salud y
notificaciones. El simulador de escritorio es el único cliente funcional de
extremo a extremo. La app Flutter actual es un **prototipo visual**: no tiene
capa HTTP y no lee ni escribe en el backend.

El bucle central es:

```text
audio o texto
    -> mensaje
    -> una o varias transacciones en estado "pendiente"
    -> confirmación humana
    -> transacciones "confirmado"
    -> puntos, presupuesto, metas, salud y notificaciones
```

Todo lo contable se **deriva** de `transacciones`; no hay saldos, cupos ni
puntajes almacenados como valores maestros. Solo cuentan las transacciones
`confirmado` y no borradas. Las propuestas pendientes no afectan ningún saldo.

Consecuencias importantes de lo que hay hoy:

- No hay procesos en segundo plano ni scheduler. Los recordatorios, las alertas
  automáticas y los cierres automáticos no se ejecutan solos.
- El cierre del día es una acción explícita; es idempotente y no recalcula
  cierres anteriores.
- El audio nunca se guarda en disco ni en la base; solo se conserva texto,
  duración y metadatos. La voz de Nancy sí se genera como WAV en memoria y no se persiste.
- Los modelos de IA corren en el PC/servidor. La ESP32 solo graba y transmite.
- La voz de Nancy corre en el PC/servidor (Piper); sin conexión, el cliente reproduce
  un banco pequeño de WAV pregrabadas y no improvisa oraciones largas.
- El firmware de la ESP32 no existe en este repositorio.

---

## 1. Arquitectura y límites del sistema

### 1.1 Componentes reales

| Ruta | Papel en la lógica actual |
|---|---|
| `backend/server.py` | Aplicación Flask, 65 rutas, autenticación, CORS, recepción de audio, orquestación, endpoints del plan de metas y TTS. |
| `backend/tts.py` | TTS local Piper y salida WAV en memoria. No guarda el audio. |
| `backend/services.py` | Dominio: mensajes, transacciones, puntos, presupuesto, metas, salud, cierre, notificaciones y orquestación del plan. |
| `backend/finance_engine.py` | Ingreso, gasto planificado, colchón y capacidad de ahorro on-the-fly. |
| `backend/optimization.py` | Modelo LP, solver HiGHS, redondeo, fallback greedy y diagnóstico del plan. |
| `backend/nlp.py` | Intención, tipo, monto, categoría, cuenta, palabra clave, metas y validación de la respuesta del LLM. |
| `backend/conversation.py` | Agente conversacional: estado en memoria, confirmaciones naturales, consultas por voz y creación de metas por diálogo. |
| `backend/ai.py` | Transcripción (Gemini o faster-whisper local) y extracción con LLM (Ollama o Gemini). |
| `backend/audio.py` | Contrato y validación del WAV. |
| `backend/auth.py` | Tokens de acceso, refresh, login y autenticación de dispositivo. |
| `backend/db.py` | Conexión SQLite, UTC, hora de Bogotá, tokens y utilidades. |
| `backend/api_utils.py` | Respuestas `ok`/`error`, lectura de JSON y formularios. |
| `database/sql/001_schema.sql` | 40 tablas, restricciones, índices y 11 triggers. |
| `database/sql/002_views.sql` | 15 vistas de cálculo. |
| `database/sql/003_seed.sql` | Catálogos semilla: categorías, cuentas y palabras. |
| `database/init_db.py` | Creación, versión de esquema y refresco de vistas. |
| `simulator/main.py` | Cliente real: graba, transcribe, interpreta, confirma y cierra el día. |
| `frontend/lib/` | Prototipo Flutter sin llamadas HTTP. |
| `tools/` | Utilidades de configuración, verificación y dataset. |

### 1.2 Flujo de una petición

```text
ESP32 (no implementada)  ─┐
simulador de escritorio  ─┼─ HTTP ─> Flask (server.py)
app Flutter (prototipo)  ─┘             │
                                        ├─ auth.py      valida token
                                        ├─ audio.py     valida WAV
                                        ├─ ai.py        transcribe / extrae
                                        ├─ nlp.py       interpreta y valida
                                        ├─ services.py  aplica reglas
                                        └─ SQLite       persiste y calcula
```

La app Flutter **no aparece en el camino real de datos**. `login_screen.dart`
solo muestra el mensaje “Inicio de sesión de demostración.” y
`home_screen.dart` usa valores fijos (`dailyBudget = 10000`,
`spent = 2500`). No hay `http`, `dio`, `api_client` ni almacenamiento de
sesión en `frontend/lib/`. La versión que sí tenía capa HTTP quedó respaldada
en la rama `respaldo-frontend-conectado`.

### 1.3 Dónde vive la IA

| Función | Proveedor | Dónde corre |
|---|---|---|
| Transcribir audio | Gemini (`google-genai`) o faster-whisper | PC/servidor |
| Interpretar la conversación | Ollama con `qwen3:4b` o Gemini | PC/servidor |
| Clasificar por reglas | `backend/nlp.py` | PC/servidor |

La interpretación por conversación tiene un contrato estricto: JSON con `intent`,
`entidades` y `confianza`. El LLM **solo interpreta**; nunca calcula montos,
fechas ni el plan. Si el LLM falla, responde `desconocido` o entrega entidades
vacías, el respaldo por reglas de `nlp.py` toma el control. Una frase larga
está impedida de confirmar o cancelar una acción pendiente solo con la opinión
del modelo; solo cuentan los disparadores de confirmación/cancelación.

La ESP32 no ejecuta modelos. Solo captura audio, lo envía por Wi-Fi y muestra
el resultado. El firmware es un pendiente del proyecto; el contrato que debería
cumplir está en `docs/DISPOSITIVO.md`.

Selección de proveedor:

- `STT_PROVEEDOR=auto` (por defecto): usa Gemini si hay clave; si la clave falla
  o el proveedor no responde, cae a faster-whisper local si está instalado.
- `STT_PROVEEDOR=local`: solo faster-whisper.
- `STT_PROVEEDOR=gemini`: solo Gemini.
- `LLM_PROVEEDOR=auto` (por defecto): prefiere Ollama; si no está disponible,
  usa Gemini si hay clave.
- `NLP_USAR_IA=off`: obliga a usar solo las reglas de `nlp.py`.

La clave de Gemini se lee de `GEMINI_API_KEY` o de
`%USERPROFILE%\.finagotchi\gemini.env`, fuera del repositorio. No debe
versionarse.

### 1.4 Contrato de audio

`backend/audio.py::validar_wav` exige:

| Propiedad | Valor |
|---|---|
| Formato | WAV (contenedor RIFF) |
| Frecuencia | 16 000 Hz |
| Canales | 1 (mono) |
| Bits por muestra | 16 |
| Duración mínima | 0.5 s |
| Duración máxima | 40 s |
| Tamaño máximo | 2 MiB (`2 * 1024 * 1024`) |

Además, el servidor configura `MAX_CONTENT_LENGTH` con ese mismo límite para
toda la petición. El archivo se lee en memoria, se valida y se pasa al
proveedor de STT; **nunca se escribe en disco ni se guarda en SQLite**. Si el
audio es inválido se responde `AUDIO_INVALIDO` (422); si supera el tamaño,
`AUDIO_MUY_GRANDE` (413). Cuando se envía audio, `message_id` es obligatorio:
es la clave de idempotencia para no transcribir dos veces el mismo mensaje.

### 1.5 Configuración de ejecución

| Variable | Efecto | Valor por defecto |
|---|---|---|
| `FINAGOTCHI_DB` | Ruta de la base | `finagotchi.db` en la raíz |
| `FINAGOTCHI_SECRET` | Firma de tokens de acceso | `finagotchi-dev-secret-v2` |
| `FINAGOTCHI_CORS_ORIGIN` | Origen permitido | `*` |
| `HOST` / `PORT` | Escucha del servidor | `0.0.0.0` / `5000` |
| `FLASK_DEBUG` | Reinicio automático | `0` (apagado) |
| `GEMINI_API_KEY` | Clave de Gemini | vacío |
| `GEMINI_MODEL` | Modelo de transcripción | `gemini-3.8-flash` |
| `STT_PROVEEDOR` | `auto`, `local` o `gemini` | `auto` |
| `STT_MODELO_LOCAL` | Tamaño de Whisper | `base` |
| `OLLAMA_URL` | Servidor de Ollama | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Modelo de extracción | `qwen3:4b` |
| `LLM_PROVEEDOR` | `auto`, `ollama` o `gemini` | `auto` |
| `NLP_USAR_IA` | `off` desactiva el LLM | `auto` |

### 1.6 Lo que no existe en el código actual

- Firmware de la ESP32.
- Scheduler, cola de trabajos o cron: nada se ejecuta “solo”.
- Verificación de correo, recuperación de contraseña y eliminación de cuenta
  (las tablas existen, los endpoints no).
- Retos, gastos fijos, comandos de dispositivo y papelera dedicada como
  endpoints (las tablas existen, el código no las usa).
- Push al dispositivo: el dispositivo consulta por polling.
- HTTPS, rate limiting general y bloqueo de cuenta por intentos de login.
- Conexión HTTP de la app Flutter actual.

---

## 2. Modelo de datos y convenciones

### 2.1 Dinero, fechas y multiusuario

- Todo monto es un entero de pesos COP. No se usan `float` para dinero.
- `fecha_hora` se guarda en UTC con formato `YYYY-MM-DDTHH:MM:SSZ`.
- `fecha_local` se guarda como `YYYY-MM-DD` en la fecha de Bogotá.
- El backend **siempre** usa `America/Bogota` (`BOGOTA` en `backend/db.py`).
  Ignora `usuarios.zona_horaria` en todos los cálculos, aunque la columna
  exista y se pueda editar.
- Todas las tablas de negocio llevan `usuario_id`. Las relaciones usan claves
  compuestas `(usuario_id, id)` para que una fila no pueda apuntar a datos de
  otro usuario. Las consultas además filtran explícitamente por `usuario_id`.
- Los borrados de movimientos y metas son lógicos: `is_deleted = 1`, no
  `DELETE`. Las cuentas sí se borran físicamente, moviendo antes sus
  transacciones a otra cuenta.

### 2.2 Grupos de tablas

| Grupo | Tablas principales |
|---|---|
| Identidad | `usuarios`, `consentimientos`, `sesiones_refresco`, `tokens_recuperacion`, `tokens_verificacion_correo`, `solicitudes_eliminacion_cuenta` |
| Perfil | `perfil_financiero`, `perfil_secciones`, `preferencias_notificacion`, `retos_respuestas` |
| Catálogos | `plantilla_categorias`, `plantilla_categoria_palabras`, `plantilla_cuentas`, `plantilla_cuenta_palabras`, `categorias`, `categoria_palabras`, `cuentas`, `cuenta_palabras` |
| Movimientos | `mensajes_dispositivo`, `transacciones`, `transacciones_versiones`, `puntos_log`, `metas_eventos`, `salud_log`, `alertas_log` |
| Metas | `metas` |
| Presupuesto | `presupuestos`, `presupuesto_categoria`, `presupuesto_diario_historial` |
| Salud y cierre | `cierres_dia`, `estado_mascota`, `salud_log`, `progreso_etapa` |
| Dispositivo | `dispositivos`, `vinculacion_codigos`, `dispositivos_telemetria`, `dispositivos_notificaciones`, `dispositivos_comandos` |
| IA | `interacciones_ia` |
| Infraestructura | `schema_migrations` |

Hay 40 tablas y 15 vistas. La versión vigente del esquema es 4
(`database/init_db.py::SCHEMA_VERSION` y `003_seed.sql`).

### 2.3 La transacción

`transacciones` es la tabla central. Campos que cambian la lógica:

| Campo | Regla |
|---|---|
| `tipo` | `gasto`, `ingreso` o `ahorro`. |
| `monto` | Entero mayor que cero. |
| `categoria_id` | Obligatoria para gasto e ingreso; debe ser del mismo tipo y estar activa. Nula para ahorro. |
| `cuenta_id` | Obligatoria; si no se envía, se usa la cuenta por defecto. |
| `meta_id` | Solo para ahorro; si se envía, la meta debe existir y no estar borrada. |
| `estado` | Solo `pendiente` o `confirmado` (restricción `CHECK`). |
| `is_deleted` | Borrado lógico. |
| `deleted_at` | Obligatorio si `is_deleted = 1` y nulo si es 0. |
| `eliminado_via` | `app`, `voz`, `deshacer` o `sistema`; solo si está borrada. |
| `origen` | `dispositivo`, `app_voz`, `manual` o `importacion`. |
| `version` | Empieza en 1; el trigger de versionado la incrementa al editar campos contables. |
| `confirmado_en` | Se llena al confirmar. |

Restricciones estructurales:

- Un ahorro **no** puede tener categoría.
- Un gasto o ingreso **no** puede tener meta.
- Un gasto o ingreso **debe** tener categoría.
- La cuenta debe pertenecer al mismo usuario.
- La categoría debe pertenecer al mismo usuario y ser del mismo tipo.

Estados reales:

```text
                 confirmar mensaje
pendiente ─────────────────────────> confirmado
    │                                    │
    │ descartar mensaje                  │ DELETE
    └──────────────┐                     └──────────────┐
                   v                                    v
             is_deleted = 1                       is_deleted = 1
             eliminado_via = 'voz'                eliminado_via = 'app'
```

No existe un estado `anulado` en la base. La constante
`services.ALLOWED_TRANSACTION_STATES` incluye `"anulado"`, pero no se usa para
escribir. La API traduce `?estado=anulado` a `is_deleted = 1`, y
`?incluir_anuladas=1` incluye las borradas. Es una vista lógica, no un estado
almacenado.

### 2.4 El mensaje

`mensajes_dispositivo` representa lo que dijo el usuario. Guarda:

- `message_id`: clave de idempotencia por usuario.
- `texto_transcrito`, `duracion_audio_s`, `confianza_ia`.
- `device_id` y `device_uid`.
- `estado`: `recibido`, `procesado`, `confirmado` o `descartado`.
- `error` cuando la interpretación no produjo movimientos.

Un mensaje puede tener varias transacciones (`transacciones.mensaje_id`), pero
el intérprete actual devuelve **como máximo una** propuesta por mensaje. El
esquema sí soporta varias; la segmentación múltiple está pendiente en
`backend/nlp.py`.

### 2.5 Los puntos

Los puntos se otorgan por trigger, no por código de aplicación:

- Al insertar una transacción `confirmado` y no borrada: +1.
- Al pasar una transacción de otro estado a `confirmado` y no borrada: +1.
- El índice único `ux_puntos_una_vez_por_tx` impide dos puntos
  `registro_valido` para la misma transacción.

No se otorgan puntos por editar, por cerrar el día, por cumplir una meta ni por
racha. La tabla `puntos_log` permite otros motivos
(`bonus_semana`, `bonus_hito`, `meta_cumplida`, `ajuste`), pero el código no los
crea.

Hay una diferencia deliberada entre dos formas de contar:

- `GET /home` y `GET /me` suman `puntos_log` en crudo, incluyendo puntos de
  transacciones que luego se borraron.
- `v_puntos_usuario` excluye los puntos cuya transacción está borrada o no
  confirmada. Es la que usa `v_progreso_etapa.puntos_totales`.

Por eso `GET /me` puede devolver un `puntos` distinto de
`progreso.puntos_totales`.

### 2.6 La salud

`estado_mascota.salud` es un valor persistido entre 0 y 100. Solo se actualiza
al cerrar el día. `GET /home` lo muestra tal cual y, en paralelo, calcula una
`proyeccion_hoy` en vivo. Ambos valores pueden diferir si hubo movimientos
después del último cierre o si el día aún no se cierra.

`salud_log` guarda cada regla aplicada, con salud anterior y nueva. El índice
`ux_salud_regla_dia` evita repetir la misma regla para la misma referencia en
el mismo día, salvo las reglas de tipo `sistema`.

### 2.7 El cierre

`cierres_dia` es una foto del día, no una tabla recalculable:

- `UNIQUE (usuario_id, fecha_local)`.
- Guarda totales, presupuesto, porcentaje, calificación, número de registros,
  salud inicial y final.
- `delta_salud` es una columna generada `salud_fin - salud_inicio`.
- Una vez creado, `close_day` devuelve el cierre existente y no lo recalcula
  aunque después se editen o borren movimientos.

### 2.8 Inicialización y migración

`create_app` solo llama a `init_db.init_sqlite` si el archivo de base **no
existe**. Si la base existe, no aplica el esquema automáticamente.

`py -3 database/init_db.py` sí revisa la versión:

- Si no hay `schema_migrations`, aplica el esquema.
- Si la versión es menor que 4, vuelve a aplicar los tres archivos SQL.
- Si es igual a 4, no hace nada.
- Si es mayor que 4, falla con un error explícito.

Por eso, después de actualizar el repositorio con cambios de esquema, hay que
ejecutar `py -3 database/init_db.py` sobre una base existente. Una base legacy
sin `usuarios` o sin `schema_migrations` no se migra automáticamente: se pide
eliminarla y recrearla.

---

## 3. Identidad, sesión y confianza

### 3.1 Registro

`POST /api/v1/auth/register` pide `nombre`, `correo` y `password`.

Validaciones implementadas:

- Campos no vacíos.
- Contraseña de al menos 8 caracteres.
- Correo único sin distinguir mayúsculas (índice único sobre `lower(correo)`).
- `nombre` se recorta a 50 caracteres.
- `correo` se guarda en minúsculas.
- `presupuesto_diario` por defecto: 30 000 COP.
- `zona_horaria` por defecto: `America/Bogota`, aunque el cálculo siempre use
  Bogotá.
- Si llega `acepta_terminos`, se inserta el consentimiento de términos.

El registro devuelve `201` con el usuario público (sin `password_hash`) y un
par de tokens. También actualiza `progreso_etapa.fecha_inicio_diagnostico` con
la fecha local.

El trigger `trg_usuarios_seed` aprovisiona automáticamente:

- Una fila de `perfil_financiero`, `preferencias_notificacion`,
  `progreso_etapa` y `estado_mascota` con salud 100.
- Seis secciones de perfil en estado `pendiente`.
- Las 16 categorías de la plantilla (12 de gasto y 4 de ingreso) y sus
  palabras clave.
- Las 5 cuentas de la plantilla: Efectivo (por defecto), Nequi, Daviplata, Nu
  y Bancolombia, con sus palabras clave.
- Una fila inicial en `presupuesto_diario_historial` con el presupuesto del
  usuario y motivo `inicial`.

### 3.2 Login y tokens

`POST /api/v1/auth/login`:

- Busca por correo sin distinguir mayúsculas.
- Verifica la contraseña con `werkzeug.security.check_password_hash`.
- Si el usuario no está en estado `activo`, responde `403 CUENTA_INACTIVA`.
- Actualiza `ultimo_acceso`.
- Devuelve tokens.

Tipos de token:

| Token | Formato | Duración | Almacenamiento |
|---|---|---|---|
| Acceso | `itsdangerous.URLSafeTimedSerializer`, sal `finagotchi-access` | 1 hora | Sin estado en la base |
| Refresh | Cadena aleatoria de 48 bytes URL-safe | 30 días | Hash SHA-256 en `sesiones_refresco` |

El token de acceso se envía como `Authorization: Bearer <token>`. No se puede
revocar antes de que expire: `logout` revoca refresh, no access.

`POST /auth/refresh` valida el refresh contra la base, lo revoca y emite un
refresh nuevo. Es rotación de un solo uso. `POST /auth/logout` revoca el
refresh indicado o todos los refresh abiertos del usuario.

`auth_required` no solo valida la firma: vuelve a consultar al usuario y exige
`estado = 'activo'`. Si la cuenta pasa a `pendiente_eliminacion`, el acceso de
la app deja de funcionar de inmediato.

### 3.3 Consentimientos

`GET /me/consents` lista los consentimientos del usuario.
`POST /me/consents` inserta o actualiza por `(usuario, tipo, versión)`. Los
tipos permitidos son `terminos`, `privacidad` y `datos_estudio_anonimo`.

No hay endpoints de verificación de correo, recuperación de contraseña ni
solicitud de eliminación de cuenta, aunque las tablas existan.

### 3.4 Vinculación del dispositivo

Flujo implementado:

1. `POST /device/register` (público) recibe `device_uid` y datos opcionales de
   modelo, firmware y MAC.
   - Si el dispositivo no existe, lo crea.
   - Si existe y **no** está vinculado, lo reutiliza y actualiza modelo o
     firmware.
   - Si existe y ya está vinculado, responde `409 DISPOSITIVO_VINCULADO`.
   - Genera un PIN de 6 dígitos con `secrets.randbelow(1_000_000)`, lo guarda
     hasheado y le da 10 minutos de vida.
2. `POST /device/pair` (requiere token de acceso) recibe `device_uid` y `pin`.
   - Busca el último código no usado y no expirado del dispositivo.
   - Máximo 5 intentos (`max_intentos` por defecto).
   - Si el PIN es correcto, vincula el dispositivo al usuario, genera un token
     de dispositivo y lo devuelve **una sola vez**.
3. El dispositivo usa `X-Device-Token: <device_token>` en las rutas
   `/device/*`.

Puntos débiles observados:

- `POST /device/register` es público y no tiene rate limiting.
- `pair` no rechaza un dispositivo que ya pertenece a otro usuario si queda un
  PIN válido sin usar. Esto puede ocurrir si se generaron varios PIN antes de
  vincular: al usar el último, los anteriores siguen vigentes y `pair` los
  acepta. El resultado es que un segundo usuario puede re-vincular el
  dispositivo.
- `device_required` valida el token del dispositivo, pero **no** verifica que
  el usuario dueño siga `activo`. Un dispositivo de una cuenta
  `pendiente_eliminacion` puede seguir operando por `/device/*`.
- `POST /messages` acepta un `device_id` de la app sin comprobar que pertenezca
  al usuario autenticado. Solo se usa para guardar `device_uid` y para intentar
  crear la notificación; si el dispositivo es de otro usuario, la notificación
  no se crea, pero el mensaje queda asociado a ese `device_id`.

---

## 4. Registro de movimientos

### 4.1 Entradas posibles

| Ruta | Autenticación | Uso |
|---|---|---|
| `POST /api/v1/messages` | Token de acceso | App o simulador; texto o audio. |
| `POST /api/v1/device/messages` | Token de dispositivo | Dispositivo; texto o audio. |
| `POST /api/v1/transactions` | Token de acceso | Registro manual directo. |

Las dos primeras crean un **mensaje** y propuestas pendientes. La tercera crea
una transacción ya confirmada por defecto.

### 4.2 Del audio al texto

`backend/server.py::procesar_mensaje_voz`:

1. Si hay archivo, exige `message_id`.
2. Busca un mensaje previo con ese `message_id` para el usuario. Si existe,
   devuelve el payload con `duplicado: true` y no vuelve a llamar a la IA.
3. Lee el archivo en memoria y llama a `audio.validar_wav`.
4. Obtiene las “hotwords” del usuario: nombres de cuentas y categorías
   (`nlp.palabras_clave_usuario`).
5. Llama a `ai.transcribe_audio`.
6. Crea el mensaje con el texto y los metadatos.
7. Registra una interacción de IA con proveedor, modelo, latencia y texto. El
   audio no se registra.

Si el STT falla, registra el error en `interacciones_ia` y responde con el
código del error (`STT_NO_CONFIGURADO`, `STT_KEY_INVALIDA`,
`STT_SIN_PERMISOS`, `STT_CUOTA`, `STT_NO_DISPONIBLE`, `STT_SIN_TEXTO`, entre
otros).

### 4.3 Interpretación de la frase

La interpretación normal ahora pasa por el agente conversacional (`backend/conversation.py`), que aplica primero su propio contexto conversacional y delega la extracción en `nlp.interpretar_con_ia` / `nlp.detectar_intencion_conversacional`. Ver `19. El agente conversacional`.

`backend/nlp.py::interpret` (ruta heredada, sin agente):

1. Normaliza el texto: minúsculas, sin tildes, espacios colapsados.
2. Detecta la intención:
   - `cerrar_dia` si contiene frases como “cerrar día” o “terminar el día”.
   - `consulta_estado` si contiene “cómo voy”, “resumen”, “balance”, etc.
   - `registrar` en cualquier otro caso.
3. Si la intención no es `registrar`, devuelve el mensaje sin transacciones.
   **El backend no ejecuta el cierre ni arma el resumen**: solo informa la
   intención. El simulador es quien llama a `/device/close-day` o a `/home`.
4. Si `NLP_USAR_IA` no es `off`, intenta la extracción con LLM.
5. Si el LLM no está disponible o su respuesta no sirve, usa las reglas.

Reglas locales:

- Tipo: `ahorro` si aparece “ahorré”, “ahorro”, “guardé”, “separé” o “meta”;
  `ingreso` si aparece “ingreso”, “recibí”, “me pagaron”, “sueldo”, “salario”,
  “quincena”, “depósito”, etc.; en cualquier otro caso, `gasto`.
- Monto: primero intenta cifras (`5.000`, `1.5 millones`) y luego palabras
  (“catorce mil”, “dos millones quinientos mil”). Si no encuentra monto,
  devuelve `requiere_aclaracion`.
- Categoría: busca palabras clave del usuario. Si la frase trae una pista
  del tipo “en accesorios” y esa palabra no es categoría ni cuenta conocida,
  devuelve `requiere_aclaracion` preguntando si se crea la categoría
  (Fase 23). Sin pista, usa “Otros” para gasto o “Otros ingresos” para
  ingreso; si no existen, la primera categoría activa del tipo.
- Cuenta: busca palabras clave; si la frase trae “por/con <palabra
  desconocida>” (p. ej. “por Nuwank”), pide aclaración en vez de
  inventar una cuenta (Fase 18). Sin pista, usa la cuenta por defecto.
- Si no hay cuenta o categoría disponible, devuelve `requiere_aclaracion`.

La extracción con LLM (`nlp.interpretar_con_ia`) valida la respuesta:

- `tipo` debe ser `gasto`, `ingreso` o `ahorro`.
- `monto` debe ser entero positivo; si el texto trae un monto, **manda el
  del texto** sobre el del LLM (Fase 18).
- `categoria` y `cuenta` deben coincidir con el catálogo real del usuario y
  **aparecer en el texto** como palabra completa: “Nuwank” no puede
  convertirse en “Nu”. Se acepta coincidencia exacta sin tildes y
  mayúsculas, o una diferencia de Levenshtein de un carácter para nombres
  de 5 o más letras.
- Una `fecha_texto` del LLM sin expresión temporal en el texto se descarta.
- Si la categoría es de otro tipo, se descarta.
- Si es ahorro, no lleva categoría.
- Si falta categoría en gasto o ingreso, se usa la de último recurso.
- Si falta cuenta, se usa la cuenta por defecto.

La IA **propone**, no confirma. Aunque el LLM devuelva una transacción, esta se
inserta como `pendiente`.

`services.create_message` valida la propuesta antes de insertar: ninguna
sugerencia sin `monto > 0` llega a `transacciones`; se degrada a
`requiere_aclaracion` con el mensaje "No se identificó un monto". Hay prueba de
regresión en `tests/test_mensajes.py`.

### 4.4 Creación del mensaje y de las propuestas

`services.create_message`:

- Es idempotente por `(usuario_id, message_id)`.
- Si no hay `device_uid`, usa `app-<user_id>`.
- Crea la fila en `mensajes_dispositivo` con estado `procesado` si la intención
  es `registrar`, o `recibido` para consulta/cierre.
- Por cada propuesta crea una transacción `pendiente`, con secuencia, texto
  original, confianza y fecha local del momento de recepción.
- No hay confirmación automática.
- Devuelve el mensaje con sus transacciones y `requiere_confirmacion`.

Si la intención es `cerrar_dia` o `consulta_estado`, el mensaje se crea pero no
se crean transacciones. El cliente debe ejecutar la acción correspondiente.

### 4.5 Confirmación humana

`POST /messages/<id>/confirm` (o `/device/messages/<id>/confirm`) llama a
`services.confirm_message`:

1. Verifica que el mensaje pertenezca al usuario.
2. Busca **todas** las transacciones `pendiente` y no borradas del mensaje.
3. Las pasa a `confirmado` con el mismo `confirmado_en`.
4. Marca el mensaje como `confirmado`.
5. Crea una notificación `movimiento_registrado` si el mensaje tiene
   `device_id` y el dispositivo pertenece al usuario.
6. Devuelve `puntos_otorgados` (cantidad de pendientes confirmadas) y una
   proyección de salud.

Después de confirmar o descartar, la ruta invalida cualquier estado
conversacional pendiente por voz (`conversation.invalidar_accion_pendiente`),
de modo que la siguiente frase no se tome como respuesta a una acción ya
resuelta.

No hay confirmación individual por endpoint: si un mensaje tuviera tres
propuestas, se confirman las tres o se descartan las tres. El `puntos_otorgados`
es informativo; los puntos reales los inserta el trigger, uno por transacción.

`POST /messages/<id>/discard` borra lógicamente solo las transacciones
`pendiente` del mensaje y marca el mensaje como `descartado`. No toca las ya
confirmadas.

### 4.6 Registro manual

`POST /transactions`:

- Exige `tipo` válido y `monto` entero positivo.
- `estado` por defecto es `confirmado`; acepta `pendiente`.
- Si no hay `cuenta_id`, usa la cuenta por defecto.
- Si es ahorro, ignora la categoría y acepta `meta_id`.
- Si no es ahorro, exige categoría activa del mismo tipo y descarta `meta_id`.
- `fecha_hora` es opcional; si no viene, usa ahora. Si viene sin zona, la
  interpreta como Bogotá.
- No crea mensaje.
- No pasa por confirmación: si se crea `confirmado`, el trigger de puntos
  otorga +1 de inmediato.

Una transacción creada con `estado = "pendiente"` por esta ruta queda huérfana:
no tiene mensaje y no hay endpoint para confirmarla. Solo se puede borrar o
dejar que bloquee el cierre del día.

### 4.7 Edición, borrado y restauración

`PATCH /transactions/<id>` permite cambiar:

- `monto`, `concepto`, `categoria_id`, `cuenta_id`, `meta_id`, `tipo` y
  `fecha_local` (Fase 17).

No permite cambiar `estado` ni `fecha_hora`. Al cambiar `tipo`, la fila
debe seguir cumpliendo el CHECK del esquema: ahorro sin categoría y
gasto/ingreso con categoría y sin meta; si falta la categoría adecuada,
se usa “Otros”/“Otros ingresos” del nuevo tipo.

- El monto debe ser positivo.
- La cuenta debe ser del usuario.
- La categoría debe existir, estar activa y ser del mismo tipo que la
  transacción.
- La meta debe existir y no estar borrada.
- El trigger `trg_tx_versionar` guarda la versión anterior en
  `transacciones_versiones` cuando cambia un campo contable. Cambiar
  `cuenta_id` no genera versión.
- La edición **no** recalcula puntos, salud ni cierres ya guardados.

`DELETE /transactions/<id>` es borrado lógico:

- Marca `is_deleted = 1`, `deleted_at` y `eliminado_via`.
- Acepta `via` en `app`, `voz`, `deshacer` o `sistema`; por defecto `app`.
- No elimina la fila ni los puntos. Los puntos dejan de contar en las vistas
  que excluyen transacciones borradas, pero siguen en el total crudo de
  `/home` y `/me`.
- No recalcula cierres.

`POST /transactions/<id>/restore` revierte el borrado lógico. Los puntos
vuelven a contar en las vistas y en el total crudo, pero no se insertan de
nuevo.

### 4.8 Listado y filtros

`GET /transactions`:

- Por defecto excluye borradas.
- `incluir_anuladas=1` incluye borradas.
- `estado=anulado` filtra `is_deleted = 1`.
- Otros `estado` filtran el estado real (`pendiente` o `confirmado`).
- Filtra por tipo, categoría, cuenta, rango de fechas y rango de monto.
- Ordena por `fecha_hora` descendente y luego por id.
- `limit` máximo 500; `offset` desde 0.

---

## 5. Dinero, presupuesto y cupo

### 5.1 Totales del día

`services.day_totals`:

```text
ingresos = SUM(monto) WHERE tipo = 'ingreso'
gastos   = SUM(monto) WHERE tipo = 'gasto'
ahorro   = SUM(monto) WHERE tipo = 'ahorro'
num_registros = COUNT(*)
balance_neto = ingresos - gastos
```

Siempre con `estado = 'confirmado'`, `is_deleted = 0` y
`fecha_local = fecha_consultada`.

El ahorro **no** resta del balance neto; se informa aparte. El balance neto es
solo ingresos menos gastos.

### 5.2 Presupuesto diario

`services.budget_for_day`:

1. Busca el último registro de `presupuesto_diario_historial` con
   `fecha_local <= fecha_consultada`.
2. Si no existe, usa `usuarios.presupuesto_diario` actual.

El trigger `trg_usuarios_budget_hist` inserta o actualiza la fila de hoy cuando
cambia `usuarios.presupuesto_diario`. Por eso el historial conserva el valor
vigente desde la fecha del cambio, pero el fallback a `usuarios.presupuesto_diario`
puede usar el valor actual para fechas anteriores al primer registro.

`cupo_restante = presupuesto_diario - gastos`. Puede ser negativo.

El porcentaje usado:

```text
si presupuesto > 0: porcentaje = int(100 * gastos / presupuesto)
si presupuesto = 0: porcentaje = 0
```

Calificación diaria:

| Porcentaje | Calificación |
|---|---|
| `<= 100` | `bien` |
| `<= 120` | `regular` |
| `> 120` | `mal` |

Con presupuesto 0 y algún gasto, el porcentaje es 0 y la calificación es
`bien`, aunque el exceso sí genera penalización de salud.

### 5.3 Presupuestos mensuales por categoría

`POST /budgets`:

- Crea un presupuesto de 2 o 3 meses.
- `fecha_inicio` por defecto hoy.
- `fecha_fin` se calcula como el día anterior al inicio más `meses`.
- `categorias` es una lista de `{categoria_id, monto_limite_mensual}`.
- El presupuesto nace **no aprobado**.

`POST /budgets/<id>/approve` lo marca aprobado y llena `aprobado_en`.

`GET /budget` devuelve el último presupuesto aprobado que cubre la fecha de hoy
y sus categorías. Si no hay, devuelve `presupuesto: null` y el presupuesto
diario del usuario.

Reglas de cálculo:

- Solo se consideran presupuestos aprobados.
- La consulta de límites usa el primer día del mes de la fecha consultada
  (`YYYY-MM-01`) y exige que esté dentro de `fecha_inicio` y `fecha_fin`.
  Si el presupuesto empieza después del día 1, ese mes no aplica límite.
- Si hay varios presupuestos aprobados superpuestos, gana el de
  `fecha_inicio` más reciente para cada categoría.
- El tope diario de una categoría es
  `monto_limite_mensual / días_del_mes`, con división decimal.
- Si el gasto confirmado del día en esa categoría supera el tope, se aplica
  `-2` de salud por categoría.
- El presupuesto por categoría **no bloquea** el registro ni la confirmación de
  un gasto. Solo afecta la salud.

No hay endpoints para editar o eliminar presupuestos.

### 5.4 Saldo de cuentas

`v_cuentas_resumen`:

```text
saldo_actual = saldo_inicial + SUM(ingreso) - SUM(gasto) - SUM(ahorro)
```

Solo con transacciones `confirmado` y no borradas. Para cuentas de tipo
`tarjeta`, `saldo_actual` es `NULL`: la tarjeta no se trata como una cuenta con
saldo disponible.

El saldo puede ser **negativo**: con `saldo_inicial = 0`, basta con que los
gastos superen a los ingresos confirmados (frecuente en las cuentas base de
la cuenta demo, sembradas con movimientos antiguos). El negativo significa
sobregiro, no un error de cálculo.

La consulta por voz distingue las 5 cuentas base sembradas por el trigger
(`es_sistema = 1`) de las creadas por el usuario y no muestra cuentas con
`oculta = 1` (Fase 19). `services.accounts_summary` obtiene `es_sistema`
con JOIN porque la vista no lo trae.

Restricciones de cuentas:

- Nombre único por usuario, sin distinguir mayúsculas.
- Una sola cuenta por defecto por usuario.
- La cuenta por defecto no puede estar oculta.
- Una tarjeta no puede tener saldo inicial distinto de cero.
- No se puede borrar la cuenta por defecto.
- Al borrar otra cuenta, todas sus transacciones (incluidas las borradas) se
  mueven a la cuenta destino. Si no se indica destino, se usa la cuenta por
  defecto.
- El borrado de cuenta es físico, no lógico.

### 5.5 Categorías

- Cada usuario nace con 16 categorías de sistema.
- Una categoría de sistema no se puede renombrar ni desactivar; su tipo no
  cambia.
- Las categorías personalizadas se pueden crear, editar, desactivar y asociar
  a palabras clave.
- Una categoría desactivada no se puede usar en transacciones nuevas, pero las
  transacciones históricas que la referencian siguen existiendo.
- El nombre es único por usuario y tipo. El `UNIQUE (usuario_id, tipo, nombre)`
  usa la colación binaria por defecto de SQLite, así que **distingue mayúsculas
  y tildes**: `Ocio` y `ocio` pueden coexistir. Las cuentas, en cambio, usan un
  índice sobre `lower(nombre)` y no distinguen mayúsculas.
- Al crear una categoría se inserta su nombre en minúsculas como palabra
  clave (`categoria_palabras`), así que “gasté en belleza” ya cae en la
  categoría creada sin intervención del LLM (Fase 23).
- Las “subcategorías” son categorías planas de gasto o ingreso; el esquema no
  tiene padre. Ahorro no usa categorías: usa metas.
- La consulta por voz (“¿cuáles son mis categorías?”, con filtro opcional
  “de gasto”/“de ingreso”) muestra por categoría el número de registros
  confirmados y el total; la voz lee las principales y el detalle completo
  queda en `datos.categorias` (Fase 23).

---

## 6. Metas y ahorro

### 6.1 Creación

`POST /goals` exige:

- `nombre` (máximo 30 caracteres).
- `monto_meta` entero positivo.
- `fecha_limite` válida.
- `frecuencia_ahorro`: `diaria`, `semanal`, `quincenal` o `mensual`.
- `aporte_periodico` entero positivo.

Opcionales: icono, día de aporte, hora de recordatorio (por defecto `08:00`) y
prioridad (por defecto 1). El nombre es único entre las metas no borradas del
usuario. La meta nace `activa`.

### 6.2 Ahorro asociado

Una transacción de tipo `ahorro`:

- No lleva categoría.
- Puede llevar `meta_id`.
- Cuenta para el saldo de la cuenta (resta).
- Cuenta para el total de ahorro del día.
- Si tiene meta, cuenta para el progreso de esa meta.

Un ahorro sin meta es un ahorro “suelto”: afecta el saldo y el total de ahorro,
pero no el progreso de ninguna meta.

### 6.3 Progreso y estado de la meta

`v_metas_progreso` calcula:

```text
ahorrado = SUM(monto) de ahorros confirmados, no borrados, con esa meta_id
faltante = monto_meta - ahorrado
porcentaje = int(100 * ahorrado / monto_meta)
```

`v_metas_estado` agrega:

- `hoy`, `inicio` y `limite` como fechas.
- `aportes_vencidos` según la frecuencia.
- `esperado = min(monto_meta, aportes_vencidos * aporte_periodico)`.
- `dias_restantes = max(0, limite - hoy)`.
- `estado_plan`:
  - `completada` si la meta ya está completada o `ahorrado >= monto_meta`.
  - `atrasada` si `ahorrado < esperado * 0.95`.
  - `vas_bien` en el resto.

### 6.4 Cálculo de aportes vencidos: dos fórmulas

Hay dos implementaciones y **no coinciden exactamente**:

**A. Reglas de salud** (`services.expected_goal_amount`):

```text
inicio = fecha de creado_en (parte YYYY-MM-DD)
fin    = min(fecha_consultada, fecha_limite)
dias   = (fin - inicio).days

diaria:    periodos = dias
semanal:   periodos = dias // 7
quincenal: periodos = dias // 15
mensual:   meses = (año_fin - año_inicio) * 12 + (mes_fin - mes_inicio)
           si dia_fin >= dia_inicio: meses += 1
           periodos = max(0, meses)

esperado = min(monto_meta, periodos * aporte_periodico)
```

**B. Vista `v_metas_estado`** (SQL):

```text
hoy = date('now','-5 hours')   -- siempre la fecha actual del servidor
diaria:    dias entre inicio y min(hoy, limite)
semanal:   esos días / 7, truncado
quincenal: esos días / 15, truncado
mensual:   meses calendario entre inicio y min(hoy, limite)
           menos 1 si el día de fin es menor que el día de inicio
```

La vista no recibe una fecha de consulta: fija `hoy` con `date('now','-5
hours')`. Por eso `esperado`, `dias_restantes` y `estado_plan` se calculan
siempre contra el día real del servidor, no contra la fecha que el cliente esté
mirando.

Consecuencia: para una meta mensual, la regla de salud suele contar **un
periodo más** que la vista. El día de creación, la regla de salud ya espera el
primer aporte mensual, mientras que la vista espera 0. Para metas diarias,
semanales y quincenales, la regla de salud empieza a contar desde el día
siguiente a la creación (el día de creación `dias = 0`).

### 6.5 Reglas de salud asociadas a metas

En `services.goal_health_rules`, solo para metas `activa` y no borradas:

- Si `ahorrado >= monto_meta`:
  - Se aplica `META_CUMPLIDA` con `+5`, una sola vez en la vida de la meta.
  - Al persistir el cierre, se inserta `metas_eventos` tipo `cumplida` y se
    marca la meta como `completada`.
- Si `esperado > 0` y `ahorrado < esperado * 0.95`:
  - Se aplica `META_ATRASADA` con `-5`, una sola vez por mes
    (`periodo_clave = YYYY-MM`).

Una meta que se cumple pero el día nunca se cierra no se marca como
`completada` ni recibe el `+5` persistido: la proyección lo muestra, pero la
persistencia ocurre solo en `close_day`.

### 6.6 Edición y borrado

`PATCH /goals/<id>` permite nombre, icono, monto, fecha límite, frecuencia,
aporte, día, hora, prioridad y estado (`activa` o `completada`). No valida de
nuevo que la fecha sea futura ni que el nuevo monto sea coherente con lo ya
ahorrado.

`DELETE /goals/<id>` es borrado lógico. Los ahorros históricos conservan su
`meta_id`, pero la meta deja de aparecer en las vistas y en las reglas de
salud.

---

## 7. Salud, ánimo y cierre del día

### 7.1 Punto de partida

`services.health_start_for_day`:

- Busca el último `cierres_dia` anterior a la fecha consultada con
  `salud_fin` no nulo.
- Si no existe, empieza en **100**.

No hay una salud diaria persistida aparte. La salud “de hoy” es una proyección
hasta que se cierra el día.

### 7.2 Reglas exactas

`services.calculate_health` aplica, en este orden:

| Código | Condición | Delta | Detalle |
|---|---|---|---|
| `EXCESO_DIARIO` | `gastos > presupuesto_diario` | `-min(20, ceil(exceso / 5000) * 2)` | `exceso = gastos - presupuesto` |
| `EXCESO_CATEGORIA` | Gasto del día en una categoría con límite aprobado supera `limite_mensual / días_del_mes` | `-2` por cada categoría | Se evalúa por categoría |
| `INACTIVIDAD` | `num_registros = 0` | `-5` | Sin transacciones confirmadas ese día |
| `RACHA` | Racha exactamente 7, 14 o 30 días | `+5`, `+10` o `+15` | Solo en esos valores exactos |
| `BALANCE_POSITIVO` | Sin exceso diario, sin exceso de categoría y `balance_neto > 0` | `+min(15, (balance_neto // 20000) * 2)` | Enteros |
| `AHORRO` | `ahorro > 0` | `+min(10, ahorro // 20000)` | Enteros |
| `META_CUMPLIDA` | Meta activa con `ahorrado >= monto_meta` | `+5` | Una vez por meta |
| `META_ATRASADA` | Meta activa con esperado > 0 y ahorrado < 95 % del esperado | `-5` | Una vez por mes |
| `TOPE_GLOBAL` | La suma bruta sale de `[-35, +25]` | Ajuste compensatorio | Deja la suma en el tope |

Después de calcular la suma bruta:

```text
bruto = suma de todos los deltas
aplicado = max(-35, min(+25, bruto))
```

Luego cada regla se aplica secuencialmente sobre la salud, con
`clamp(salud, 0, 100)` en cada paso. Por eso una salud que empieza en 10 y
recibe varios castigos termina en 0, y una que empieza en 95 y recibe +15
termina en 100.

Ejemplos rápidos:

- Presupuesto 30 000, gastos 41 000: exceso 11 000;
  `ceil(11000/5000) = 3`, penalización `-6`.
- Gasto 200 000 con presupuesto 0: exceso 200 000;
  `ceil(200000/5000) = 40`, pero el tope de la regla es `-20`.
- Ahorro de 45 000: `45 000 // 20 000 = 2`, bonus `+2`.
- Ahorro de 19 999: `0`, sin bonus.
- Racha de 8 días: no hay bonus, porque la regla solo mira 7, 14 y 30.

### 7.3 Racha

`services.streak_ending_on`:

- Toma las fechas locales distintas con al menos una transacción confirmada y
  no borrada, hasta la fecha consultada.
- Empieza en la fecha consultada y cuenta hacia atrás mientras cada día
  consecutivo tenga registro.
- Si la fecha consultada no tiene ningún registro, la racha es **0**, aunque
  haya habido actividad los días anteriores.

No se guarda una racha diaria separada. `progreso_etapa.racha_actual` y
`mejor_racha` solo se actualizan al cerrar el día.

### 7.4 Ánimo

`services.mood_for_health` y `v_estado_mascota` usan los mismos cortes:

| Salud | Ánimo |
|---|---|
| `<= 20` | `CRITICO` |
| `<= 50` | `TRISTE` |
| `<= 80` | `PREOCUPADO` |
| `> 80` | `FELIZ` |

`v_estado_mascota` además expone `alerta_critica = 1` cuando la salud es
`<= 20`.

### 7.5 Cierre del día

`POST /days/<fecha>/close` o `POST /device/close-day` llama a
`services.close_day`:

1. Si ya existe un cierre para ese usuario y fecha, lo devuelve sin cambiar
   nada.
2. Si hay transacciones `pendiente` no borradas de esa fecha, falla con
   “Hay movimientos pendientes sin resolver”.
3. Calcula la salud con `persist=True`.
4. Inserta `cierres_dia` con los totales y la salud.
5. Inserta las reglas en `salud_log` (con `INSERT OR IGNORE` por el índice
   único).
6. Actualiza `estado_mascota.salud`.
7. Actualiza `progreso_etapa.racha_actual` y `mejor_racha`.
8. Devuelve el cierre con reglas y ánimo.

No hay validación de que la fecha sea hoy ni de que sea pasada. Se puede cerrar
una fecha futura o una fecha muy anterior. Tampoco se recalculan cierres
posteriores si se edita un movimiento de un día ya cerrado.

### 7.6 `GET /home`

`services.home_payload` devuelve:

- `usuario`: id, nombre y zona horaria configurada.
- `mascota`: fila de `v_estado_mascota` (salud persistida y ánimo).
- `proyeccion_hoy`: salud calculada en vivo para hoy.
- `hoy`: ingresos, gastos, ahorro, balance neto, presupuesto diario, cupo
  restante y número de registros.
- `progreso`: fila de `v_progreso_etapa`.
- `puntos`: suma cruda de `puntos_log`.
- `fecha_local`: fecha de Bogotá.

`mascota.salud` y `proyeccion_hoy.salud` pueden diferir. La primera es la
última salud persistida; la segunda es lo que pasaría si se cerrara hoy con los
movimientos actuales.

### 7.7 Métricas

| Ruta | Qué devuelve |
|---|---|
| `GET /metrics/daily?fecha=` | Resumen diario y desglose por categoría. Usa `v_balance_diario` si existe la fila; si no, calcula con `day_totals`. |
| `GET /metrics/weekly?fecha=` | Ventana de 7 días que termina en la fecha; totales, balance, capacidad libre de ahorro y gastos por día. |
| `GET /metrics/monthly?fecha=` | Desde el día 1 del mes hasta la fecha; totales y categorías. |
| `GET /metrics/health?fecha=` | Cierre persistido (si existe) y proyección. |
| `GET /metrics/diagnostics` | Progreso, puntos de `v_puntos_usuario` y últimos 30 cierres. |

La documentación antigua llama `/metrics/diagnosis`; la ruta real es
`/metrics/diagnostics`.

---

## 8. Notificaciones y dispositivo

### 8.1 Notificaciones al dispositivo

`services.create_device_notification`:

- Solo crea la notificación si el dispositivo existe y pertenece al usuario.
- Deduplica por `(dispositivo_id, tipo, mensaje_id, transaccion_id)`.
- Inserta en `dispositivos_notificaciones` con estado `pendiente`.

El único tipo que el código crea hoy es `movimiento_registrado`, al confirmar
un mensaje con `device_id`. Los tipos de edición, borrado, batería,
desconexión, vinculación y desvinculación están permitidos por el esquema, pero
no se generan.

`GET /device/notifications`:

- Requiere token de dispositivo.
- Sin `estado`, devuelve `pendiente` y `entregada`.
- Acepta `estado`, `after_id` y `limit` (máximo 100).
- Devuelve `ultima_id` para que el dispositivo pueda paginar.

`POST /device/notifications/<id>/ack`:

- `entregada`: solo desde `pendiente`.
- `leida`: desde `pendiente` o `entregada`.
- No se puede volver atrás.

`POST /device/notifications/ack` hace lo mismo en lote.

No hay push: el dispositivo debe consultar por polling.

### 8.2 Telemetría

`POST /device/telemetry`:

- Requiere token de dispositivo.
- Actualiza batería, estado, firmware, última conexión y registros pendientes.
- Inserta una fila en `dispositivos_telemetria`.
- Si el dispositivo está vinculado, devuelve salud, ánimo, cupo restante y
  resumen de hoy.
- El `commit` de la telemetría ocurre antes de comprobar si el dispositivo
  está vinculado; en un caso anómalo podría guardar telemetría y responder
  `403 DISPOSITIVO_NO_VINCULADO`.

`POST /finagotchi/telemetry` es un alias legacy de la misma función.

### 8.3 Desvinculación

`POST /device/unlink` requiere token de acceso y `device_uid`:

- Pone `usuario_id = NULL` y `estado_conexion = 'desconectado'`.
- El trigger `trg_dispositivos_fabrica` limpia token, vinculación, método y
  registros pendientes.

Después de desvincular, el dispositivo conserva su `device_uid` y puede
volver a registrarse y recibir un PIN nuevo.

### 8.4 Comandos y alertas

Las tablas `dispositivos_comandos` y `alertas_log` existen y tienen
restricciones, pero **no hay endpoints ni servicios que las usen**. Las
preferencias de notificación se pueden leer y editar, pero ningún proceso las
aplica.

---

## 9. Perfil financiero y bienestar

### 9.1 Perfil

`PATCH /me/profile` acepta cualquier columna de `perfil_financiero` excepto
`usuario_id` e `ingreso_total_mensual`. La segunda es una columna generada a
partir de:

```text
ingreso_total_mensual = ingreso_trabajo_mensual + apoyo_familiar_mensual
                      + beca_mensual + otros_ingresos_mensual
```

`GET /me/profile` devuelve el perfil y la completitud que calcula
`v_perfil_completitud`.

Problema observado: el trigger crea las seis secciones en `pendiente`, pero
**ningún endpoint actualiza `perfil_secciones`** al llenar el perfil. Por eso
la completitud se queda en 0 % salvo que se modifique directamente la base
(por ejemplo, el dataset de demostración).

### 9.2 Bienestar

`v_bienestar_financiero` combina seis componentes:

| Componente | Fórmula | Peso |
|---|---|---|
| Estrés | `(10 - estres_financiero) / 9 * 100` | 0.25 |
| Seguridad | `se_siente_seguro * 100` | 0.20 |
| Dificultad | `(5 - dificultad_llevar_cuentas) / 4 * 100` | 0.15 |
| Deuda | 100 si no tiene deuda de tarjeta; 50 si paga a cuotas; 0 si debe y no paga a cuotas | 0.15 |
| Fondo | 100 si tiene fondo de emergencia; 0 si no | 0.15 |
| Ahorro | `min(100, 100 * ahorro_mensual / (0.10 * ingreso_total_mensual))` | 0.10 |

Los componentes nulos se excluyen y los pesos se renormalizan:

```text
puntaje = round(suma(componente * peso) / suma(pesos_disponibles))
cobertura = round(suma(pesos_disponibles) * 100)
```

Si no hay ningún componente respondido, `puntaje` es `NULL` y `cobertura` es 0.
El endpoint devuelve esos valores tal cual.

---

## 10. Inventario de endpoints reales

Hay 65 rutas: las 61 originales más `GET /goals/plan`, `POST /goals/plan/simulate`,
`POST /voice/synthesize` y `POST /device/voice/synthesize`. Leyenda de
autenticación: `—` público, `A` token de acceso, `D` token de dispositivo.

### 10.1 Públicas

| Método | Ruta | Auth | Función |
|---|---|---|---|
| GET | `/api/v1/health` | — | Estado y versión de esquema. |
| GET | `/api/v1/ready` | — | Disponibilidad y versión. |
| POST | `/api/v1/auth/register` | — | Registro y tokens. |
| POST | `/api/v1/auth/login` | — | Login y tokens. |
| POST | `/api/v1/auth/refresh` | — | Rotación de refresh. |
| POST | `/api/v1/device/register` | — | Alta de dispositivo y PIN. |

### 10.2 Cuenta y perfil

| Método | Ruta | Auth | Función |
|---|---|---|---|
| POST | `/api/v1/auth/logout` | A | Revoca refresh. |
| GET | `/api/v1/me` | A | Usuario, perfil, mascota, progreso y puntos. |
| PATCH | `/api/v1/me` | A | Nombre, teléfono, zona horaria y presupuesto diario. |
| GET | `/api/v1/me/profile` | A | Perfil y completitud. |
| PATCH | `/api/v1/me/profile` | A | Actualiza columnas del perfil. |
| GET | `/api/v1/me/consents` | A | Lista consentimientos. |
| POST | `/api/v1/me/consents` | A | Registra o actualiza consentimiento. |
| GET | `/api/v1/me/wellbeing` | A | Puntaje y cobertura de bienestar. |
| GET | `/api/v1/home` | A | Resumen del día y proyección; con `?incluir_plan=1` agrega `plan_ahorro`. |

### 10.3 Cuentas y categorías

| Método | Ruta | Auth | Función |
|---|---|---|---|
| GET | `/api/v1/accounts` | A | Cuentas con saldo calculado. |
| POST | `/api/v1/accounts` | A | Crea cuenta. |
| PATCH | `/api/v1/accounts/<id>` | A | Edita cuenta. |
| DELETE | `/api/v1/accounts/<id>` | A | Borra cuenta y mueve movimientos. |
| GET | `/api/v1/categories` | A | Categorías activas. |
| POST | `/api/v1/categories` | A | Crea categoría y palabras. |
| PATCH | `/api/v1/categories/<id>` | A | Edita categoría. |
| POST | `/api/v1/categories/<id>/deactivate` | A | Desactiva categoría no sistema. |

### 10.4 Movimientos y mensajes

| Método | Ruta | Auth | Función |
|---|---|---|---|
| GET | `/api/v1/transactions` | A | Lista con filtros. |
| POST | `/api/v1/transactions` | A | Crea movimiento manual. |
| GET | `/api/v1/transactions/<id>` | A | Detalle. |
| PATCH | `/api/v1/transactions/<id>` | A | Edita monto, concepto, categoría, cuenta o meta. |
| DELETE | `/api/v1/transactions/<id>` | A | Borrado lógico. |
| POST | `/api/v1/transactions/<id>/restore` | A | Restaura borrado lógico. |
| POST | `/api/v1/messages` | A | Crea mensaje por texto o audio. |
| GET | `/api/v1/messages/<id>` | A | Mensaje y transacciones. |
| POST | `/api/v1/messages/<id>/confirm` | A | Confirma todas las pendientes. |
| POST | `/api/v1/messages/<id>/discard` | A | Descarta pendientes. |
| POST | `/api/v1/voice/synthesize` | A | Sintetiza la respuesta en WAV (memoria). |

### 10.5 Días, métricas, metas y presupuesto

| Método | Ruta | Auth | Función |
|---|---|---|---|
| GET | `/api/v1/days/<fecha>` | A | Cierre o proyección del día y categorías. |
| POST | `/api/v1/days/<fecha>/close` | A | Cierra el día. |
| GET | `/api/v1/metrics/daily` | A | Métricas diarias. |
| GET | `/api/v1/metrics/weekly` | A | Ventana de 7 días. |
| GET | `/api/v1/metrics/monthly` | A | Mes hasta la fecha. |
| GET | `/api/v1/metrics/health` | A | Cierre y proyección de salud. |
| GET | `/api/v1/metrics/diagnostics` | A | Progreso, puntos y cierres. |
| GET | `/api/v1/goals` | A | Metas con estado calculado. |
| POST | `/api/v1/goals` | A | Crea meta. |
| GET | `/api/v1/goals/plan` | A | Plan óptimo de ahorro con programación lineal. |
| POST | `/api/v1/goals/plan/simulate` | A | Plan con overrides, sin escribir en la base. |
| GET | `/api/v1/goals/<id>` | A | Detalle de meta. |
| PATCH | `/api/v1/goals/<id>` | A | Edita meta. |
| DELETE | `/api/v1/goals/<id>` | A | Borrado lógico de meta. |
| GET | `/api/v1/budget` | A | Presupuesto aprobado vigente. |
| POST | `/api/v1/budgets` | A | Crea presupuesto de 2 o 3 meses. |
| POST | `/api/v1/budgets/<id>/approve` | A | Aprueba presupuesto. |
| GET | `/api/v1/notifications/settings` | A | Preferencias. |
| PATCH | `/api/v1/notifications/settings` | A | Edita preferencias. |

### 10.6 Dispositivo

| Método | Ruta | Auth | Función |
|---|---|---|---|
| POST | `/api/v1/device/pair` | A | Vincula con PIN. |
| GET | `/api/v1/device` | A | Lista dispositivos del usuario. |
| POST | `/api/v1/device/unlink` | A | Desvincula. |
| POST | `/api/v1/device/telemetry` | D | Telemetría y resumen. |
| GET | `/api/v1/device/notifications` | D | Polling de notificaciones. |
| POST | `/api/v1/device/notifications/<id>/ack` | D | Acuse individual. |
| POST | `/api/v1/device/notifications/ack` | D | Acuse en lote. |
| POST | `/api/v1/device/messages` | D | Mensaje por texto o audio. |
| POST | `/api/v1/device/messages/<id>/confirm` | D | Confirma pendientes. |
| POST | `/api/v1/device/voice/synthesize` | D | Sintetiza la respuesta en WAV (memoria). |
| POST | `/api/v1/device/close-day` | D | Cierra el día de hoy. |
| POST | `/api/v1/finagotchi/telemetry` | D | Alias legacy de telemetría. |

### 10.7 Rutas documentadas que no existen

- `/notifications` y `/notification-preferences` (solo existe
  `/notifications/settings`).
- `/trash` (la papelera se consulta con `GET /transactions?estado=anulado`).
- `/transactions/bulk-confirm` (la confirmación es por mensaje).
- `/device/commands`.
- `/metrics/diagnosis` (la ruta real es `/metrics/diagnostics`).
- Recuperación de contraseña, verificación de correo y eliminación de cuenta.

---

## 11. Invariantes y restricciones de la base

Estas son las reglas que la base hace cumplir aunque el código de aplicación
tenga un descuido.

### 11.1 Aislamiento por usuario

- `transacciones`, `cuentas`, `categorias`, `metas` y otras tablas tienen
  `UNIQUE (usuario_id, id)` para permitir claves foráneas compuestas.
- Las FKs incluyen `usuario_id`, de modo que una transacción no puede apuntar
  a una cuenta, categoría o meta de otro usuario.
- Los triggers impiden cambiar `usuario_id` en transacciones, cuentas,
  categorías y metas.

### 11.2 Movimientos

- `monto > 0`.
- `tipo` en `gasto`, `ingreso`, `ahorro`.
- `estado` en `pendiente`, `confirmado`.
- `(is_deleted = 1) = (deleted_at IS NOT NULL)`.
- `is_deleted = 1 OR eliminado_via IS NULL`.
- Ahorro sin categoría; gasto e ingreso con categoría y sin meta.
- `version >= 1`.
- `concepto` de máximo 255 caracteres.
- `origen` en `dispositivo`, `app_voz`, `manual`, `importacion`.

### 11.3 Mensajes

- `message_id` único por usuario.
- `estado` en `recibido`, `procesado`, `confirmado`, `descartado`.
- `duracion_audio_s` entre 0.5 y 40 si no es nula.
- `confianza_ia` entre 0 y 1.
- `device_id` puede ser nulo; `device_uid` es obligatorio.

### 11.4 Cuentas y categorías

- Nombre de cuenta único por usuario, sin distinguir mayúsculas.
- Una sola cuenta por defecto.
- La cuenta por defecto no puede estar oculta.
- Tarjeta con saldo inicial 0.
- Categorías de sistema no se renombran ni cambian de tipo.
- Nombre de categoría único por usuario y tipo, con comparación sensible a
  mayúsculas y tildes (`UNIQUE (usuario_id, tipo, nombre)`).

### 11.5 Metas

- `monto_meta > 0`, `aporte_periodico > 0`.
- Frecuencia en `diaria`, `semanal`, `quincenal`, `mensual`.
- Estado en `activa`, `completada`.
- Nombre único entre metas no borradas.
- `(is_deleted = 1) = (deleted_at IS NOT NULL)`.

### 11.6 Puntos y salud

- Un solo punto `registro_valido` por transacción.
- `puntos_log.motivo` en `registro_valido`, `bonus_semana`, `bonus_hito`,
  `meta_cumplida`, `ajuste`.
- `salud_log.salud_anterior` y `salud_nueva` entre 0 y 100.
- Una regla por día y referencia, salvo las de tipo `sistema`.
- `cierres_dia` único por usuario y fecha.
- `porcentaje_usado >= 0`.
- `calificacion` en `bien`, `regular`, `mal`.

### 11.7 Presupuesto

- `meses` en 2 o 3.
- `fecha_fin > fecha_inicio`.
- `aprobado = 1` si y solo si `aprobado_en` no es nulo.
- Límite mensual `>= 0`.
- Una categoría no se repite dentro del mismo presupuesto.
- Una fila de historial diario por usuario y fecha.

### 11.8 Notificaciones y dispositivo

- `dispositivos.device_uid` único.
- `estado_conexion` en `conectado`, `sin_conexion`, `desconectado`.
- `estado_dispositivo` en `reposo`, `grabando`, `procesando`, `transmitiendo`,
  `bloqueado`.
- `nivel_bateria` entre 0 y 100.
- Estado de notificación coherente con sus timestamps:
  - `pendiente`: sin `entregado_en` ni `leido_en`.
  - `entregada`: con `entregado_en`, sin `leido_en`.
  - `leida`: con ambos.
- `max_intentos > 0` en códigos de vinculación.

### 11.9 Triggers

| Trigger | Efecto |
|---|---|
| `trg_usuarios_seed` | Aprovisiona perfil, preferencias, progreso, mascota, secciones, categorías, cuentas y presupuesto inicial. |
| `trg_usuarios_budget_hist` | Registra el cambio de presupuesto diario en el historial de hoy. |
| `trg_tx_versionar` | Guarda la versión anterior al editar campos contables. |
| `trg_dispositivos_fabrica` | Limpia el dispositivo al desvincular. |
| `trg_tx_usuario_inmutable` | Impide mover una transacción de usuario. |
| `trg_cuentas_usuario_inmutable` | Impide mover una cuenta de usuario. |
| `trg_categorias_usuario_inmutable` | Impide mover una categoría de usuario. |
| `trg_metas_usuario_inmutable` | Impide mover una meta de usuario. |
| `trg_categorias_sistema_bloqueada` | Impide renombrar o cambiar el tipo de una categoría de sistema. |
| `trg_tx_puntos_insert` | +1 punto al insertar una transacción confirmada. |
| `trg_tx_puntos_confirm` | +1 punto al confirmar una transacción. |

---

## 12. Flujos de extremo a extremo

### 12.1 Registro y primer acceso

1. `POST /auth/register` con nombre, correo y contraseña.
2. Se crea el usuario y el trigger aprovisiona todo.
3. Se devuelven `access_token` y `refresh_token`.
4. El cliente guarda los tokens y llama a `GET /home`.
5. `GET /home` devuelve mascota en 100, presupuesto de 30 000, categorías y
   cuentas listas, sin movimientos.

### 12.2 Registrar por voz y confirmar

1. El cliente graba un WAV de 16 kHz, mono, 16 bits, de 0.5 a 40 s.
2. `POST /messages` con `audio`, `message_id` y opcionalmente `device_id`.
3. El backend valida el audio, transcribe, interpreta y crea un mensaje con
   una transacción `pendiente`.
4. La respuesta trae `requiere_confirmacion: true` y la propuesta.
5. El cliente muestra la propuesta al usuario.
6. `POST /messages/<id>/confirm` confirma todas las pendientes.
7. El trigger inserta los puntos; se crea la notificación si hay dispositivo.
8. `GET /home` refleja el gasto, el cupo y la nueva proyección de salud.

Si el usuario no confirma, no se afecta ningún saldo. Si descarta, las
pendientes se borran lógicamente.

### 12.3 Registrar manualmente

1. `POST /transactions` con tipo, monto, cuenta y categoría.
2. Por defecto queda `confirmado` y el trigger otorga +1.
3. No hay mensaje ni paso de confirmación adicional.
4. `GET /home` lo refleja de inmediato.

### 12.4 Cerrar el día

1. El usuario o el dispositivo llama a `POST /days/<fecha>/close` o
   `POST /device/close-day`.
2. Si hay pendientes, falla.
3. Se calcula la salud, se guarda el cierre, se actualiza la mascota y la
   racha.
4. El cierre queda congelado. Si luego se edita un movimiento, el cierre no
   cambia.

### 12.5 Crear una meta y ahorrar

1. `POST /goals` con nombre, monto, fecha, frecuencia y aporte.
2. El usuario registra un `ahorro` con `meta_id` (por voz o manual).
3. El ahorro resta del saldo de la cuenta y suma al progreso de la meta.
4. `GET /goals` muestra `ahorrado`, `esperado`, `dias_restantes` y
   `estado_plan`.
5. Al cerrar el día, si la meta está cumplida, se marca `completada` y se
   aplica `+5` una vez. Si está atrasada, se aplica `-5` una vez por mes.

### 12.6 Vincular un dispositivo

1. El dispositivo llama `POST /device/register` con su `device_uid`.
2. Recibe un PIN de 6 dígitos válido 10 minutos.
3. El usuario, ya autenticado, llama `POST /device/pair` con el `device_uid` y
   el PIN.
4. Recibe `device_token` una sola vez.
5. El dispositivo usa `X-Device-Token` para telemetría, mensajes,
   notificaciones y cierre.
6. `POST /device/unlink` lo devuelve a fábrica.

### 12.7 Crear y aprobar un presupuesto

1. `POST /budgets` con `fecha_inicio`, `meses` 2 o 3 y categorías.
2. El presupuesto queda no aprobado.
3. `POST /budgets/<id>/approve` lo aprueba.
4. `GET /budget` lo devuelve si cubre la fecha de hoy.
5. Las reglas de salud empiezan a usar sus límites mensuales por categoría.

### 12.8 Crear una meta por voz

1. El usuario dice: “quiero una meta para comprar unos audífonos”.
2. Nancy pregunta, una por una: monto → plazo → frecuencia → prioridad.
3. Python calcula la fecha límite desde el plazo; el LLM nunca calcula fechas.
4. La meta se simula como virtual (`meta_id = -1`); el LP evalúa capacidad
   mensual y prioridades y devuelve un diagnóstico (aporte esperado,
   cumplimiento ponderado, faltante). No se escribe nada aún.
5. Nancy vuelve a preguntar “¿la creo?”.
6. Con “sí”/“ok”/“correcto” se persiste con `services.create_goal` y se crea
   el flujo normal de ahorro (12.5).

Si el usuario cancela en cualquier punto, la meta no existe en la base.

---

## 13. Diferencias entre especificación, esquema y código

| Tema | Especificación o documentación | Código actual |
|---|---|---|
| Estado de transacción | Se habla de anulación | Solo `pendiente` y `confirmado`; “anulado” es `is_deleted = 1` en la API. |
| Confirmación | Se describe confirmación por movimiento | Es por mensaje: confirma todas las pendientes del mensaje. |
| Confirmación por voz | Se especula en el texto "OK" | Acepta frases naturales: sí, ok, correcto, está bien, confirmo. |
| Consulta de estado | Se describe solo en la app | El agente responde por voz/texto y calcula sin escribir. |
| Frontend | La especificación describe un cliente completo | La app actual es un prototipo visual sin HTTP; la versión conectada está en `respaldo-frontend-conectado`. |
| Zona horaria | `usuarios.zona_horaria` por usuario | El backend siempre usa `America/Bogota`. |
| Recordatorios | Se especifican notificaciones y recordatorios | No hay scheduler; solo se crea `movimiento_registrado` al confirmar. |
| Alertas | `alertas_log` con muchos tipos | Ningún código inserta en `alertas_log`. |
| Comandos | `dispositivos_comandos` | Sin endpoints ni uso. |
| Retos y gastos fijos | Tablas y flujos en la especificación | Sin endpoints ni uso. |
| Eliminación de cuenta | Tabla `solicitudes_eliminacion_cuenta` | Sin endpoint. |
| Verificación de correo | Tabla `tokens_verificacion_correo` | Sin endpoint; `correo_verificado` queda en 0. |
| Recuperación de contraseña | Tabla `tokens_recuperacion` | Sin endpoint. |
| Completitud del perfil | Se espera que avance al llenar el perfil | `perfil_secciones` no se actualiza; queda en 0 %. |
| Límite por categoría | Se describe como límite | No bloquea gastos; solo resta salud. |
| Meta mensual | Una sola noción de aportes vencidos | Dos fórmulas distintas: salud y vista. |
| Puntos | Se espera que reflejen solo movimientos válidos | `/home` y `/me` suman crudo; `v_puntos_usuario` filtra borrados. |
| Validación de entrada | Se espera 422 para datos inválidos | `ValueError` se traduce a 400, pero un `null` en un campo numérico opcional (por ejemplo `presupuesto_diario`) produce `TypeError` y 500. |
| Cierre | Se espera que se recalcule | Es una foto idempotente; no se recalcula. |
| `/metrics/diagnosis` | Documentado | La ruta real es `/metrics/diagnostics`. |
| Papelera | Endpoint `/trash` documentado | Se usa `GET /transactions?estado=anulado`. |
| Confirmación individual | Documentada | No existe endpoint para confirmar una transacción suelta. |
| Audio | Se describe el contrato | Implementado y probado; el archivo no se guarda. |
| IA en dispositivo | Se aclara que no | Correcto: la IA corre en el PC/servidor. |

---

## 14. Limitaciones y riesgos actuales

### 14.1 Funcionales

1. **No hay automatización temporal.** Nada se ejecuta al llegar una hora:
   recordatorios, alertas, cierres y resúmenes requieren una petición.
2. **El cierre no se recalcula.** Un movimiento editado después del cierre
   deja el cierre y la salud persistida desactualizados.
3. **La confirmación es todo o nada por mensaje.** No se puede confirmar una
   propuesta y descartar otra del mismo mensaje.
4. **El NLP devuelve una sola transacción por mensaje.** El esquema soporta
   varias, pero la segmentación no está implementada.
5. **Una transacción manual `pendiente` no se puede confirmar.** No tiene
   mensaje y no hay endpoint de confirmación individual; solo se puede borrar.
6. **Los puntos y la salud no se recalculan al editar o borrar.** Los triggers
   de puntos solo actúan al insertar o confirmar; los cierres son fotos.
7. **La salud solo se materializa al cerrar.** `GET /home` muestra una
   proyección, no la salud persistida.
8. **La meta mensual tiene dos criterios.** La regla de salud es más exigente
   que la vista de metas.
9. **La completitud del perfil no avanza.** No hay actualización de
   `perfil_secciones`.
10. **No se puede cerrar un día con pendientes.** Es intencional, pero un
    pendiente huérfano puede bloquear el cierre hasta que se borre.
11. **El presupuesto por categoría no impide gastar.** Solo castiga la salud.
12. **No hay historial de presupuesto diario para fechas anteriores al primer
    registro.** Se usa el presupuesto actual como fallback.
13. **El cierre acepta fechas futuras o pasadas sin validación.**
14. **La app Flutter no es un cliente real.** Es un prototipo visual.
15. **Una propuesta de IA sin monto ya no rompe la base.** Está validada antes de insertar; degrada a `requiere_aclaracion`. Ver sección 19.
16. **Algunos campos numéricos opcionales responden 500 si llegan en `null`.**
    `int(None)` lanza `TypeError`, que no captura el manejador de `ValueError`.
    Por ejemplo, `POST /auth/register` con `presupuesto_diario: null` devuelve
    `ERROR_INTERNO` en vez de 422.
17. **El plan de metas no se persiste.** Se recalcula en cada petición; no hay
    historial de planes ni comparación con el plan anterior.
18. **La calidad del plan depende del perfil.** Un ingreso mal declarado o un
    presupuesto irreal producen un plan poco realista. Por eso se usa el
    criterio conservador y se reporta la confianza.
19. **El plan solo cubre metas.** No optimiza gastos fijos, inventarios ni
    gastos hormiga.
20. **El primer mes se prorratea.** Si el usuario consulta el plan a fin de
    mes, la capacidad del primer mes puede ser pequeña y concentrar el ahorro
    en los meses siguientes.
21. **El diálogo vive en memoria.** Si el backend se reinicia, el borrador
     conversacional pendiente se pierde (el mensaje pendiente y su
     confirmación siguen disponibles por API; solo se pierde el contexto de
     qué se estaba respondiendo).
22. **La clasificación del LLM no es un contrato.** Puede responder `confirmar`
     ante una frase larga; el agente ignora esa clasificación y exige que la
     frase misma sea afirmativa corta. Aún así, la basura semántica puede
     forzar aclaraciones o rutas asistidas; los accesos destructivos dependen
     del turno de confirmación, no del LLM.
23. **Una transacción por mensaje.** La segmentación multi-movimiento está
     pendiente; “gasté y también ahorré” es una sola transacción.


### 14.2 Seguridad y operación

1. **Secreto por defecto.** Si no se define `FINAGOTCHI_SECRET`, los tokens de
   acceso se firman con un valor conocido y versionado.
2. **CORS abierto por defecto.** `FINAGOTCHI_CORS_ORIGIN=*` permite cualquier
   origen.
3. **Sin HTTPS.** El servidor de desarrollo escucha HTTP.
4. **Sin rate limiting general.** Solo el PIN tiene 5 intentos.
5. **Registro de dispositivo público.** Cualquiera que conozca un `device_uid`
   puede generar un PIN si el dispositivo no está vinculado.
6. **Re-vinculación con PIN viejo.** Si quedan PIN válidos sin usar, otro
   usuario puede vincular el dispositivo.
7. **Dispositivo de cuenta inactiva.** `device_required` no valida el estado
   del usuario dueño.
8. **`device_id` sin verificación de dueño en `/messages`.** La app puede
   asociar un mensaje a un dispositivo ajeno.
9. **El refresh token se guarda hasheado, pero el PIN de 6 dígitos tiene un
   espacio pequeño.** El límite de intentos lo mitiga, no lo elimina.
10. **La base de datos está versionada en git.** Cada cambio de esquema aparece
    en el diff y los datos de demostración se publican con el repositorio.
11. **El backend es monoproceso y síncrono.** Las llamadas a IA pueden tardar
    segundos y bloquean la petición; no hay cola.
12. **El modelo local y Ollama son dependencias externas.** Si no están
    instalados, la voz y la extracción pueden fallar o degradarse a reglas.

### 14.3 Dispositivo y audio

1. **No hay firmware.** La ESP32 no está implementada.
2. **40 s de WAV no caben en SRAM.** 16 kHz × 16 bits × mono × 40 s = 1.28 MB;
   la SRAM declarada es 512 KB. Hay que hacer streaming o usar flash.
3. **El navegador no entrega WAV.** Chrome y Edge suelen dar webm/opus; el
   backend solo acepta WAV. La voz funciona en Android/iOS o con entrada
   manual.
4. **El audio se mantiene en memoria.** El límite de 2 MiB acota el riesgo,
   pero no hay streaming.

---

## 15. Trazabilidad regla → código

| Regla de negocio | Implementación principal |
|---|---|
| Aislamiento por usuario | FKs compuestas en `001_schema.sql`; filtros `usuario_id` en `server.py` y `services.py` |
| Solo confirmado y no borrado cuenta | `services.day_totals`, `002_views.sql` (`v_balance_diario`, `v_movimientos`, etc.) |
| Confirmación humana por mensaje | `services.confirm_message`; rutas `/messages/<id>/confirm` y `/device/messages/<id>/confirm` |
| Descarte de propuestas | `server.py::discard_message` |
| Un punto por transacción confirmada | `trg_tx_puntos_insert` y `trg_tx_puntos_confirm` |
| Presupuesto diario | `services.budget_for_day`; `trg_usuarios_budget_hist` |
| Límite diario por categoría | `services.approved_category_limits` y `services.spending_by_category` |
| Cálculo de salud | `services.calculate_health` |
| Reglas de metas en salud | `services.goal_health_rules` y `services.expected_goal_amount` |
| Ánimo | `services.mood_for_health` y `v_estado_mascota` |
| Racha | `services.streak_ending_on` |
| Cierre idempotente | `services.close_day` |
| Saldo de cuentas | `v_cuentas_resumen` |
| Progreso de metas | `v_metas_progreso` y `v_metas_estado` |
| Bienestar | `v_bienestar_financiero` |
| Completitud del perfil | `v_perfil_completitud` |
| Capacidad de ahorro | `finance_engine.monthly_capacity` |
| Plan óptimo de metas | `optimization.plan_goals` y `services.goal_plan` |
| Simulación de plan | `POST /goals/plan/simulate` y `services.goal_plan` |
| Contrato de audio | `backend/audio.py::validar_wav` |
| Interpretación por reglas | `backend/nlp.py::interpret` |
| TTS local Piper | `backend/tts.py::sintetizar_wav` y rutas `/voice/synthesize` |
| Extracción con LLM | `backend/nlp.py::interpretar_con_ia` y `backend/ai.py::extraer_estructura` |
| Agente conversacional | `backend/conversation.py::procesar_turno` |
| Confirmación natural | `conversation._es_confirmacion` y `conversation._es_cancelacion` |
| Invalidación de estado por confirmación API | `conversation.invalidar_accion_pendiente` |
| Metas por diálogo con viabilidad LP | `conversation._recopilar_meta`, `services.simulate_goal_draft`, `services.create_goal` |
| Consultas sin escritura | `conversation._consulta_*` con `services.metrics_daily`, `period_totals`, `budget_for_day` y vistas |
| Transcripción con fallback | `backend/ai.py::transcribe_audio` |
| Idempotencia de mensajes | `mensajes_dispositivo` `UNIQUE (usuario_id, message_id)` y `services.create_message` |
| Borrado lógico | `services.delete_transaction`, `services.restore_transaction` |
| Versionado de ediciones | `trg_tx_versionar` |
| Vinculación de dispositivo | `server.py::register_device` y `pair_device` |
| Notificaciones | `services.create_device_notification` y `device_notifications` |
| Telemetría | `server.py::device_telemetry` |
| Inicialización de esquema | `database/init_db.py` |

---

## 16. Cómo verificar el comportamiento

### 16.1 Suite de pruebas

```powershell
py -3 -m unittest discover -s tests -v
```

La suite cubre esquema, API, audio, IA, seguridad, CORS, codificación,
simulador, comandos, dataset y optimización. Al cierre de este documento son
**206 pruebas**.

### 16.2 Backend en marcha

```powershell
py -3 backend/server.py
```

En otra terminal:

```powershell
curl.exe http://localhost:5000/api/v1/health
curl.exe http://localhost:5000/api/v1/ready
```

### 16.3 Flujo mínimo con el simulador

```powershell
py -3 simulator/main.py
```

El simulador usa el backend real, graba o recibe texto, muestra la propuesta,
pide confirmación y permite cerrar el día. Es la forma más rápida de ver la
lógica completa sin firmware.

### 16.4 Verificación de dataset

```powershell
py -3 -m unittest tests.test_dataset_bd -v
```

Este comando comprueba conteos, integridad referencial, coincidencia de saldos,
puntos, metas, cierres y exportaciones CSV.

---

## 17. Catálogo de algoritmos financieros

Esta sección responde, para cada cálculo: **qué hace, con qué fórmula, cuándo se
calcula y dónde se aplica**. La etiqueta de momento distingue:

- **On-the-fly:** se recalcula en cada petición.
- **Persistido:** queda guardado y no se recalcula.
- **Híbrido:** se proyecta en vivo, pero se guarda una foto al cerrar.

### 17.1 Matriz resumen

| # | Algoritmo | Objetivo | Momento | Aplicación |
|---|---|---|---|---|
| 1 | Totales del día | Sumar ingresos, gastos y ahorro confirmados | On-the-fly | `/home`, métricas, salud |
| 2 | Presupuesto vigente | Obtener el límite diario aplicable | On-the-fly + historial | Cupo y salud |
| 3 | Cupo restante | Saber cuánto queda del día | On-the-fly | `/home`, dispositivo |
| 4 | Límite por categoría | Comparar gasto diario contra el tope mensual prorrateado | On-the-fly | Salud |
| 5 | Saldo de cuentas | Reconstruir el saldo desde el saldo inicial | On-the-fly (vista) | `/accounts` |
| 6 | Progreso de meta | Medir ahorro acumulado y porcentaje | On-the-fly (vista) | `/goals`, salud |
| 7 | Aportes vencidos | Comparar ahorro contra lo esperado | On-the-fly (vista) | Estado de meta y salud |
| 8 | Salud | Puntaje 0–100 con eventos del día | Híbrido | Mascota y cierre |
| 9 | Racha | Días consecutivos con actividad | On-the-fly | Bonus de salud |
| 10 | Ánimo | Traducir salud a estado visible | On-the-fly | Mascota |
| 11 | Bienestar | Promedio ponderado de seis componentes | On-the-fly (vista) | `/me/wellbeing` |
| 12 | Puntos | Recompensar transacciones confirmadas | Persistido + agregación | `/home`, `/me` |
| 13 | Cierre del día | Guardar foto de totales y salud | Persistido | Historial y auditoría |
| 14 | Ingreso estimado | Estimar ingreso mensual conservador | On-the-fly | Capacidad de ahorro |
| 15 | Gasto planificado | Estimar el gasto mensual sin doble conteo | On-the-fly | Capacidad de ahorro |
| 16 | Capacidad de ahorro | Calcular el excedente mensual disponible | On-the-fly | Plan de metas |
| 17 | Plan óptimo de metas | Asignar ahorro entre metas | On-the-fly (LP) | `/goals/plan` |

### 17.2 Totales del día

- **Objetivo:** resumir la actividad confirmada de una fecha.
- **Entradas:** `transacciones` con `estado = 'confirmado'`, `is_deleted = 0` y
  `fecha_local = d`.
- **Fórmulas:**

```text
I(d) = Σ monto si tipo = 'ingreso'
G(d) = Σ monto si tipo = 'gasto'
A(d) = Σ monto si tipo = 'ahorro'
B(d) = I(d) − G(d)
n(d) = COUNT(*)
```

- **Salida:** `ingresos`, `gastos`, `ahorro`, `balance_neto`, `num_registros`.
- **Momento:** on-the-fly.
- **Aplicación:** `/home`, `/metrics/*`, salud, cierre.
- **Código:** `services.day_totals`.
- **Supuesto:** el ahorro no resta del balance neto; se informa aparte.

### 17.3 Presupuesto diario

- **Objetivo:** decidir el límite de gasto de una fecha.
- **Fórmula:**

```text
P(d) = último monto de presupuesto_diario_historial con fecha_local ≤ d
       o, si no existe, usuarios.presupuesto_diario
```

- **Salida:** entero COP.
- **Momento:** on-the-fly; el historial lo mantiene
  `trg_usuarios_budget_hist`.
- **Aplicación:** cupo, salud, métricas.
- **Código:** `services.budget_for_day`.

### 17.4 Cupo restante y límite por categoría

- **Cupo:**

```text
Cupo(d) = P(d) − G(d)
```

Puede ser negativo; no bloquea gastos.

- **Límite por categoría:** con `L_c` el límite mensual aprobado y
  `D(d)` los días del mes:

```text
tope_diario(c, d) = L_c / D(d)
si G_c(d) > tope_diario(c, d):
    salud −= 2
```

- **Momento:** on-the-fly.
- **Aplicación:** `/home`, `/budget`, reglas de salud.
- **Código:** `services.approved_category_limits`,
  `services.spending_by_category`, `services.calculate_health`.

### 17.5 Saldo de cuentas

- **Objetivo:** reconstruir el dinero disponible por cuenta.
- **Fórmula:**

```text
S(cuenta) = saldo_inicial
          + Σ ingresos confirmados
          − Σ gastos confirmados
          − Σ ahorros confirmados
```

Para `tipo_cuenta = 'tarjeta'`, el saldo es `NULL` porque representa deuda, no
liquidez.

- **Momento:** on-the-fly en `v_cuentas_resumen`.
- **Aplicación:** `/accounts`, simulador.
- **Código:** `database/sql/002_views.sql`.

### 17.6 Progreso de meta

- **Objetivo:** medir cuánto falta para cada meta.
- **Fórmula:**

```text
s_i = Σ ahorros confirmados de la meta i
f_i = M_i − s_i
pct_i = ⌊100 · s_i / M_i⌋
```

- **Momento:** on-the-fly en `v_metas_progreso`.
- **Aplicación:** `/goals`, salud, plan de metas.
- **Código:** `v_metas_progreso`.

### 17.7 Aportes vencidos y estado del plan

- **Objetivo:** comparar el ahorro real con el esperado según la frecuencia.
- **Fórmula de la vista:**

```text
esperado_i = min(M_i, periodos_i × aporte_periodico_i)
estado_plan_i =
    'completada' si estado = 'completada' o s_i ≥ M_i
    'atrasada'   si s_i < 0.95 · esperado_i
    'vas_bien'   en otro caso
```

- **Fórmula de salud:** `services.expected_goal_amount` calcula los periodos
  con otra convención de redondeo. Es una diferencia conocida y documentada.
- **Momento:** on-the-fly, pero la vista usa `date('now','-5 hours')` para
  “hoy”, no una fecha recibida. Por eso no permite consultas históricas
  deterministas.
- **Aplicación:** `/goals`, reglas de salud.
- **Código:** `v_metas_estado`, `services.expected_goal_amount`.

### 17.8 Salud

- **Objetivo:** puntaje de 0 a 100 que refleja el comportamiento financiero.
- **Fórmula:**

```text
H' = clamp(H_prev + Δ, 0, 100)
Δ  = max(−35, min(25, Σ δ_evento))
```

Eventos típicos: transacción confirmada, exceso de presupuesto, exceso por
categoría, meta atrasada, cierre con saldo positivo.

- **Salida:** salud proyectada y salud persistida.
- **Momento:** híbrido. `/home` y `/metrics/health` proyectan; el cierre guarda
  una foto en `salud_log`.
- **Aplicación:** mascota, cierre, bienestar.
- **Código:** `services.calculate_health`, `services.health_projection`,
  `services.close_day`.

### 17.9 Racha

- **Objetivo:** contar días consecutivos con al menos una transacción
  confirmada, terminando en la fecha consultada.
- **Fórmula:**

```text
racha(d) = 0 si no hay transacción confirmada en d
           n si d, d−1, …, d−n+1 tienen actividad y d−n no
```

- **Momento:** on-the-fly.
- **Aplicación:** bonus de salud y progreso.
- **Código:** `services.streak_ending_on`.

### 17.10 Ánimo

- **Objetivo:** traducir la salud a un estado visible para la mascota.
- **Fórmula:**

```text
salud ≤ 20  → CRITICO
salud ≤ 50  → TRISTE
salud ≤ 80  → PREOCUPADO
salud > 80  → FELIZ
```

- **Momento:** on-the-fly.
- **Aplicación:** `/home`, pantallas del dispositivo.
- **Código:** `services.mood_for_health`, `v_estado_mascota`.

### 17.11 Bienestar financiero

- **Objetivo:** índice de 0 a 100 con varios componentes.
- **Fórmula:**

```text
bienestar = round(Σ componente_k × peso_k / Σ pesos_disponibles)
```

Si un componente no tiene dato, se excluye y se reduce la cobertura.

- **Momento:** on-the-fly en `v_bienestar_financiero`.
- **Aplicación:** `/me/wellbeing`.
- **Código:** `v_bienestar_financiero`.

### 17.12 Puntos

- **Objetivo:** recompensar el registro y la confirmación.
- **Fórmula:** `+1` por transacción confirmada y no borrada, insertado por
  trigger en `puntos_log`.
- **Salida:** suma de puntos.
- **Momento:** persistido; la suma se hace en vivo.
- **Aplicación:** `/home`, `/me`, progreso de etapa.
- **Código:** `trg_tx_puntos_insert`, `trg_tx_puntos_confirm`.

### 17.13 Cierre del día

- **Objetivo:** dejar una foto auditable del día.
- **Fórmula:** copia `I(d)`, `G(d)`, `A(d)`, `B(d)` y la salud final en
  `cierres_dia` y `salud_log`.
- **Momento:** persistido e idempotente; no se recalcula si luego cambian los
  movimientos.
- **Aplicación:** historial, métricas de cierre.
- **Código:** `services.close_day`.

### 17.14 Ingreso estimado

- **Objetivo:** estimar el ingreso mensual con criterio conservador.
- **Fórmula:**

```text
ingreso_declarado = perfil_financiero.ingreso_total_mensual
ingreso_observado = round(Σ ingresos de 90 días × 30 / 90)

ingreso_estimado =
    min(declarado, observado)  si ambos existen
    declarado                  si solo existe el declarado
    observado                  si solo existe el observado
    0                          si no hay datos
```

- **Momento:** on-the-fly.
- **Aplicación:** capacidad de ahorro.
- **Código:** `finance_engine.estimate_income`,
  `finance_engine.observed_monthly_income`.

### 17.15 Gasto planificado

- **Objetivo:** estimar el gasto mensual sin sumar dos veces el presupuesto
  diario y los límites por categoría.
- **Fórmula:**

```text
gasto_planificado =
    Σ límites mensuales aprobados       si hay presupuesto mensual vigente
    presupuesto_diario × días_del_mes   en caso contrario
    0                                   si no hay presupuesto
```

- **Momento:** on-the-fly.
- **Aplicación:** capacidad de ahorro.
- **Código:** `finance_engine.planned_monthly_expense`.

### 17.16 Capacidad de ahorro

- **Objetivo:** saber cuánto puede ahorrar el usuario cada mes.
- **Fórmula:**

```text
colchon = colchon_pct × ingreso_estimado
C_t = max(0, ingreso_estimado − gasto_planificado − colchon)
```

El primer mes se prorratea:

```text
C_1 = max(0, C_1 × días_restantes / días_del_mes)
```

- **Salida:** lista de meses con ingreso, gasto, colchón y capacidad.
- **Momento:** on-the-fly.
- **Aplicación:** plan de metas, `/home?incluir_plan=1`.
- **Código:** `finance_engine.monthly_capacity`.

### 17.17 Plan óptimo de metas

- **Objetivo:** asignar la capacidad mensual entre metas.
- **Modelo:** programación lineal; ver sección 18 y
  `docs/OPTIMIZACION_IO.md`.
- **Entradas:** metas, capacidad mensual, prioridad y fecha límite.
- **Salida:** asignación por meta y mes, cumplimiento, faltante y diagnóstico.
- **Momento:** on-the-fly en cada petición; no se persiste.
- **Aplicación:** `/goals/plan`, `/goals/plan/simulate`,
  `/home?incluir_plan=1` y la opción `[P]` del simulador.
- **Código:** `optimization.plan_goals`, `services.goal_plan`.

---

## 18. Optimización de metas con programación lineal

### 18.1 Decisión

Se implementó la **opción 1** de la propuesta de Investigación de Operaciones:
optimización de presupuesto y metas de ahorro con programación lineal. La IO es
parte funcional del backend, no solo documentación.

Quedan fuera de alcance, por ahora, EOQ, inventarios, reposición de efectivo,
gastos hormiga y pronósticos estocásticos.

### 18.2 Modelo

```text
max Z = Σ_i p_i · y_i − ε · Σ_i Σ_t (t / H) · x_{i,t}

s.a.
Σ_i x_{i,t} ≤ C_t
S_i + Σ_t x_{i,t} ≥ M_i · y_i
Σ_t x_{i,t} ≤ M_i − S_i
0 ≤ y_i ≤ 1
x_{i,t} ≥ 0
x_{i,t} = 0 si t > T_i
```

Donde `x_{i,t}` es el dinero asignado a la meta `i` en el mes `t`, `y_i` la
fracción de cumplimiento, `p_i` la prioridad, `M_i` el monto, `S_i` el ahorrado
y `C_t` la capacidad.

### 18.3 Solver y redondeo

- `scipy.optimize.linprog(method="highs")` en dos etapas: primero maximiza el
  cumplimiento ponderado; luego minimiza el tiempo de asignación sin perder
  cumplimiento.
- Si SciPy no está disponible o el LP falla, se usa un fallback greedy
  determinista por prioridad descendente y fecha límite ascendente.
- Los flotantes se redondean hacia abajo y el remanente se reparte por mayor
  parte fraccionaria, verificando que ninguna suma mensual supere `C_t`.

### 18.4 Endpoints

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/v1/goals/plan` | Plan con datos reales. Parámetros `meses` (1–24), `fecha` y `colchon_pct` (0–50). |
| POST | `/api/v1/goals/plan/simulate` | Plan con overrides de ingreso, gasto, capacidad, prioridades o metas. |
| GET | `/api/v1/home?incluir_plan=1` | Resumen compacto del plan. |

Ambos endpoints de plan son de solo lectura, requieren autenticación y **no
crean transacciones ni mueven saldos**.

### 18.5 Reglas de negocio de la IO

1. La confirmación humana sigue siendo obligatoria para cualquier movimiento
   real. El plan solo propone.
2. La prioridad se valida entre 1 y 5 al crear o editar una meta.
3. Una meta vencida no recibe asignación.
4. Una meta completada no consume capacidad.
5. Si no hay ingreso, el plan devuelve capacidad cero y diagnóstico
   `PERFIL_INCOMPLETO`.
6. Si no hay metas, devuelve `metas = []` y diagnóstico `SIN_METAS`, no un
   error.
7. El plan es determinista: mismos datos, mismo resultado.

### 18.6 Detalle completo

El desarrollo matemático, los contratos JSON, los ejemplos numéricos y el
trabajo futuro están en `docs/OPTIMIZACION_IO.md`.

---



## 19. El agente conversacional

Desde la versión 1.2 el camino de voz no va directo de `/messages` a
`nlp.interpret`. Todas las frases — voz y texto — pasan por el agente
(`backend/conversation.py`), que conserva el estado del diálogo y decide entre
ejecutar, preguntar o confirmar.

### 19.1 Dónde vive y dónde no vive el estado

El estado vive **en memoria**, identificado por `(usuario_id,
dispositivo_uid)`, con TTL de 30 minutos. No está versionado ni
timestamped. **No es fuente de verdad financiera**: los movimientos
pendientes siguen en `mensajes_dispositivo` y `transacciones`; si el backend
se reinicia solo se pierde el borrador en curso y el mensaje pendiente queda
huyendo en la base. La confirmación siempre es legible desde la API aunque el
estado en memoria haya expirado, y desde la Fase 22 la voz también recupera
el pendiente huérfano (ver 19.12).

### 19.2 Los estados

| Estado | Significado |
|---|---|
| `inactiva` | No hay acción pendiente. |
| `confirmando_movimiento` | Se propuso un movimiento; espera "sí", "ok" o corrección. |
| `recopilando_meta` | El usuario está completando una meta nueva (nombre, monto, plazo, frecuencia, prioridad). |
| `confirmando_meta` | La meta está simulada; espera confirmación. |
| `confirmando_accion` | Hay otra escritura pendiente (eliminar/editar movimiento, cuenta, categoría, presupuesto, perfil, meta). |

La identidad del dispositivo es la clave: dos dispositivos del mismo usuario
no pueden usar el diálogo del otro.

### 19.3 El ciclo de un turno

1. `procesar_turno` recibe texto (transcriptor), `device_id` y `origen`.
2. Si el mensaje ya existe por `message_id`, devuelve el payload guardado;
   no vuelve a llamar a la IA (idempotencia).
3. Con estado `confirmando_*`, una frase de confirmación se evalua antes que
   cualquier otra cosa:
   - **Confirmación natural**: "sí", "ok", "okay", "correcto", "está bien",
     "confirmo", "dale". Nada fuera de estas (y ningún vocabulario en
     negativo).
   - **Cancelación natural**: "no", "cancela", "cancelar", "olvídalo",
     "descarta".
   - **Corrección**: "cambia el monto a 25 mil", "la cuenta es Nequi",
     "no es de ayer, es de hoy", "con la categoría de Belleza"; el dato nuevo
     se aplica a la propuesta antes de confirmarla (Fase 17 y 23).
4. Frase larga solo confirma si empieza por una afirmación corta
   (`_es_confirmacion`): "gasté 20 mil" nunca confirma. El LLM no puede
   marcar como confirmación una frase larga aunque así lo diga.
5. Si el intent es de consulta, el backend **calcula sin escribir** y responde
   en lenguaje natural.
6. Si intenta escribir, se crea una propuesta y el estado pasa a
   `confirmando_*`. Nada se persiste hasta que la persona confirme.
7. `_recordar` mantiene un historial corto (máximo 12 turnos) en memoria para
   depuración; no se escribe en la base.

### 19.4 Consultas naturales (sin escribir)

| Pregunta | Respuesta |
|---|---|
| "¿cómo me fue hoy?" | gastos, ahorro e balance del día del usuario + cupo restante. |
| "balance de esta semana" | totales del rango Lunes→hoy (7 días). |
| "balance del mes" | totales del mes calendario. |
| "¿cómo van mis metas?" | progreso, porcentaje y estado `v_metas_estado`. |
| "¿cuánto debo ahorrar este mes?" | plan LP: capacidad y aportes recomendados. |
| "muéstrame lo que hay pendiente" | movimientos pendientes sin confirmar; consultar no los resuelve (Fase 21). |
| "¿cuáles son mis cuentas?" | cuentas base vs. propias, sin ocultas, con saldo (Fase 19). |
| "¿cuáles son mis categorías?" (filtro "de gasto"/"de ingreso") | categorías con nº de registros y total confirmado; por voz, las principales (Fase 23). |
| movimientos, presupuesto, perfil | resúmenes desde catálogos reales. |

Las consultas devuelven `tipo_respuesta: "consulta"`, `intent` legible y
`datos` con los números exactos; **nunca escribe**. Pedir “categorías de
ahorro” no lista categorías: responde que el ahorro usa metas.

### 19.5 Creación de metas por diálogo

1. "quiero una meta para comprar unos audífonos" abre `recopilando_meta`.
2. Nancy pregunta, uno por uno, lo que falta: **monto → plazo → frecuencia → prioridad**.
   Nunca acepta inventar un dato; si el usuario lo dijo en la misma frase, la
   respuesta se entiende de una vez; si falta, se pregunta.
3. El plazo se evalúa en Python (`nlp.parse_plazo`), no en el LLM.
4. La meta se simula como meta virtual con `meta_id = -1`
   (`services.simulate_goal_draft`); el LP (`optimization.plan_goals`) asigna
   capacidad respetando prioridades, colchón e ingresos declarados, y
   **proponga** sin escribir.
5. Nancy narra la viabilidad (aportes estimados, cumplimiento esperado,
   déficit) y pregunta "¿la creo?".
6. Solo al confirmar con "sí"/"ok"/"correcto" se crea la meta
   (`services.create_goal`) y se transiciona a `inactiva`.

### 19.6 Otras operaciones por voz (Fase 11)

Todas pasan por la misma ruta de confirmación que un registro:

| Intención | Acción tras confirmar |
|---|---|
| `editar_movimiento` | Aplica `changes` (monto / categoría / cuenta) con `services.update_transaction`. |
| `eliminar_movimiento` | `is_deleted = 1` vía `services.delete_transaction` (vía `voz`). |
| `crear_cuenta` | `services.create_account` validada contra el catálogo. |
| `crear_categoria` | `services.create_category` validada contra el catálogo. |
| `actualizar_presupuesto` | `services.set_daily_budget` (ingresa a historial). |
| `actualizar_perfil` | `services.set_profile_income`. |
| `eliminar_meta` | `services.delete_goal` (borrado lógico). |

Nada se ejecuta sin la frase de confirmación.

### 19.7 Cómo se apaga la IA

| Variable | Efecto |
|---|---|
| `NLP_USAR_IA=off` | El agente usa solo `nlp.detectar_intencion_conversacional`, determinístico. |
| Sin `LLM_PROVEEDOR`/`OLLAMA_URL` válido | El intento IA devuelve `None`; el agente cae a reglas. |
| LLM responde `desconocido` o entidades vacías | El respaldo por reglas toma el turno (antes: el error devolvía "No entendí"). |

### 19.8 Contrato de respuesta al cliente

Toda respuesta agrega:

```json
{
  "mensaje_nancy": "...",
  "tipo_respuesta": "confirmacion|resultado|consulta|aclaracion|error|ayuda",
  "estado_conversacion": "inactiva|confirmando_movimiento|...",
  "datos": { "transaccion|borrador|resumen|cierre": ... },
  "requiere_confirmacion": true|false
}
```

Los campos previos (`transacciones`, `intent`, `id`, `duplicado`, ...) se conservan.

### 19.9 Confirmación externa (API)

`POST /api/v1/messages/<id>/confirm`, `POST /api/v1/device/messages/<id>/confirm`
y `POST /api/v1/messages/<id>/discard` llaman a
`conversation.invalidar_accion_pendiente`, que busca sesiones en memoria del
usuario cuyo pedido pendiente coincide con ese mensaje y las borra (sin
importar el dispositivo). Sin esto, el estado quedaba colgado y la siguiente
frase se tomaba como respuesta a un pendiente que ya no existía.

### 19.10 Guardas y límites

- **Idempotencia** por `message_id`: la respuesta de una retransmisión es la
  misma primera respuesta, sin repetir IA.
- **Ventana de palabras de confirmación** limitada a 8 palabras y con
  `len(palabras) <= 6` para frases cortas; el LLM no sobreescribe.
- **Una transacción por mensaje**: la segmentación multi-movimiento está
  pendiente.
- **TTL 30 minutos**: el diálogo pendiente se olvida solo.
- **Sin escritura fuera de confirmación**: ninguna ruta nueva escribe sin
  frase afirmativa; inclusive el cierre de día exige la palabra de confirmación.

### 19.11 Voz de Nancy

El backend usa `backend/tts.py` con **Piper** y un modelo local español
(por defecto `es_MX-claude-high.onnx`). La WAV se genera en memoria y no se
guarda en disco ni en SQLite. Sin Piper o sin el modelo, el backend responde
sin el bloque `voz` y el cliente sigue mostrando el texto.

La voz se solicita por petición separada para no inflar el mensaje ni guardar
nada:

- `POST /api/v1/voice/synthesize` (token de acceso).
- `POST /api/v1/device/voice/synthesize` (token de dispositivo).

Ambas aceptan hasta 400 caracteres y devuelven `audio/wav`. El backend no
persiste el audio.

Sin conexión, `simulator/assets/voz/*.wav` reproduce un banco corto
pregrabado (¿Está correcto?, Listo, Entendido, No entendí ...). Ante una
oración natural o un dato nuevo (nombre, monto, fecha), el cliente muestra el
texto; no intenta sintetizar offline.

Las respuestas incluyen `voz` cuando el backend está listo para hablar, lo que
el simulador aprovecha con `[V]` para activar o silenciar.

### 19.12 Fases 17 a 23: correcciones, validación, pendientes, cuentas y categorías

**Fase 17 — Correcciones completas.** `_corregir_movimiento` corrige
monto, categoría, cuenta, meta, fecha, tipo y concepto (antes solo monto y
categoría). Las frases de corrección incluyen “no está bien”,
“no es de ayer, es de hoy”, “la cuenta es Nequi” y “con la categoría de …”.
`resolver_rango` ignora la fecha negada (“no es de ayer, es de hoy” → hoy).
Una frase de registro completa con un pendiente abierto descarta el
pendiente anterior y abre uno nuevo, en vez de dejar dos borradores.
`services.update_transaction` acepta `tipo` y `fecha_local` manteniendo el
CHECK del esquema (ahorro sin categoría; gasto/ingreso con categoría y sin
meta).

**Fase 18 — El LLM propone, el texto manda.** En `_interpretar` el monto del
texto sobrescribe el del LLM; una cuenta o fecha del LLM que no aparece en
el texto se descarta. En `construir_movimiento` la cuenta del LLM debe
aparecer como palabra completa (“Nuwank” no es “Nu”); una pista
“por/con <palabra desconocida>” o “en <categoría desconocida>” pide
aclaración en vez de caer en la cuenta por defecto o en “Otros”.

**Fase 19 — Mis cuentas.** `accounts_summary` filtra `oculta = 0` y expone
`es_sistema` con JOIN. La consulta distingue “cuentas base” (las 5 sembradas
por el trigger) de “cuentas propias”. Saldos negativos = sobregiro con
`saldo_inicial = 0`.

**Fase 21 — Consultar pendientes.** `consultar_pendientes` lista los
movimientos `pendiente` (detalle en pantalla, conteo + más reciente por
voz) y **no** los resuelve: el estado en memoria se conserva. Va antes de
confirmar/cancelar para que “qué me falta por confirmar” sea consulta, no
aceptación.

**Fase 22 — Pendiente huérfano.** Sin estado en memoria, un “sí”,
“cancela” o corrección busca los pendientes en la base: si hay
**exactamente uno**, reconstruye la acción y ejecuta el flujo normal; si
hay varios, pide aclaración sin confirmar nada; si no hay ninguno, responde
lo de siempre. Nunca se confirma sin la frase afirmativa del usuario.

**Fase 23 — Categorías.** La consulta muestra nº de registros y total
confirmado por categoría (filtro opcional gasto/ingreso; ahorro → metas).
Crear categoría por voz acepta “agrega esta categoría X en gasto”,
“agrega la subcategoría X de ingreso” o “crea una categoría llamada X de
gasto”; las “subcategorías” son categorías planas y ahorro no admite
categorías. La categoría nueva inserta su nombre como palabra clave.
Una categoría de corrección inexistente se crea y se aplica al pendiente
(`aplicar_a_message_id`) antes de pedir el “sí” final del movimiento.

---


## Apéndice A. Dataset de demostración


La base `finagotchi.db` del repositorio contiene un dataset sintético
reproducible:

- 25 usuarios.
- 18 dispositivos (nunca más dispositivos que usuarios; máximo uno por
  usuario).
- 500 transacciones: 459 confirmadas vigentes, 22 confirmadas en papelera y 19
  pendientes.
- 343 mensajes.
- 575 interacciones de IA.
- 81 metas, 15 cumplidas.
- 546 filas en `puntos_log` que suman 1 151 puntos.
- 151 cierres de día.
- 173 alertas.
- 15 vistas.
- 40 tablas.

La exportación por tabla está en `datasets/dataset_bd/` (40 CSV, 6 268 filas,
`manifest.json` con SHA-256). El consolidado en formato largo está en
`datasets/dataset_bd/consolidado/dataset_completo.csv` (65 017 filas,
separador `;`, UTF-8 con BOM), con su propio manifiesto.

El dataset es datos de demostración, no una fuente de reglas de negocio. Sirve
para probar consultas, vistas y exportaciones con volúmenes realistas.

## Apéndice B. Archivos que conviene leer en este orden

1. `backend/server.py`: rutas y orquestación.
2. `backend/services.py`: reglas de dominio.
3. `backend/finance_engine.py`: ingreso, gasto, colchón y capacidad.
4. `backend/optimization.py`: programación lineal de metas.
5. `backend/nlp.py`: interpretación.
6. `backend/ai.py`: proveedores de IA.
7. `backend/audio.py`: contrato del WAV.
8. `database/sql/001_schema.sql`: tablas, restricciones y triggers.
9. `database/sql/002_views.sql`: cálculos derivados.
10. `simulator/main.py`: cliente real.
11. `tests/test_api.py`, `tests/test_finance_engine.py` y
    `tests/test_optimization.py`: comportamiento esperado.
12. `docs/OPTIMIZACION_IO.md`: detalle de la IO.

## Apéndice C. Glosario operativo

| Término | Significado en este código |
|---|---|
| Movimiento | Fila de `transacciones` de tipo gasto, ingreso o ahorro. |
| Propuesta | Transacción `pendiente` creada a partir de un mensaje. |
| Confirmar | Pasar todas las pendientes de un mensaje a `confirmado`. |
| Descartar | Borrar lógicamente las pendientes de un mensaje. |
| Papelera | Conjunto de transacciones con `is_deleted = 1`. |
| Cupo | `presupuesto_diario - gastos`; puede ser negativo. |
| Cierre | Foto persistida de un día en `cierres_dia`. |
| Proyección | Cálculo de salud en vivo, sin persistir. |
| Racha | Días consecutivos con al menos una transacción confirmada, terminando en la fecha consultada. |
| Meta atrasada | Ahorro menor al 95 % del esperado. |
| Dispositivo vinculado | Fila de `dispositivos` con `usuario_id` no nulo y token válido. |
| Token de acceso | Credencial de 1 hora para la API de usuario. |
| Token de dispositivo | Credencial persistente para las rutas `/device/*`. |
