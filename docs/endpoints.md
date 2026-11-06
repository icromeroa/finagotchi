# FinaGotchi · Endpoints de la API

Guía práctica del backend para conectar la app Flutter. El detalle funcional
completo está en `docs/ESPECIFICACIONES.md`, sección 11. Este archivo es el
resumen que se necesita para programar el cliente.

## 1. Arranque

```powershell
py -3 backend/server.py
```

Por defecto escucha en `http://localhost:5000`. Todas las rutas cuelgan de
`/api/v1`.

Verificar que está vivo:

```powershell
curl.exe http://localhost:5000/api/v1/health
```

```json
{ "ok": true, "data": { "estado": "ok", "schema_version": 4 } }
```

### Dirección desde la app

| Dónde corre la app | `API_BASE_URL` |
|---|---|
| Chrome en el mismo PC | `http://localhost:5000/api/v1` |
| Emulador Android | `http://10.0.2.2:5000/api/v1` |
| Celular en la misma red Wi-Fi | `http://IP_DEL_PC:5000/api/v1` |

El servidor ya escucha en `0.0.0.0` y en el puerto `5000`. Se puede cambiar el
puerto con la variable de entorno `PORT`:

```powershell
$env:PORT="5001"
py -3 backend/server.py
```

CORS está habilitado para cualquier origen y responde el permiso de red
privada que exige Chrome desde la versión 115. No hace falta configurar nada
más para probar desde el navegador.

## 2. Formato de respuesta

Éxito:

```json
{ "ok": true, "data": { } }
```

Error:

```json
{
  "ok": false,
  "error": {
    "codigo": "CREDENCIALES_INVALIDAS",
    "mensaje": "Correo o contraseña incorrectos",
    "detalles": {}
  }
}
```

Siempre es JSON, incluso en los errores 500. El campo `codigo` es el que debe
usar la app para decidir qué mostrar; `mensaje` ya viene en español y se puede
mostrar tal cual.

## 3. Autenticación

### Registrar

`POST /api/v1/auth/register`

```json
{
  "nombre": "Ana",
  "correo": "ana@ejemplo.com",
  "password": "secreto123",
  "presupuesto_diario": 30000
}
```

La contraseña debe tener mínimo 8 caracteres. `presupuesto_diario` es
opcional. Responde `201` con el usuario y los tokens.

### Iniciar sesión

`POST /api/v1/auth/login`

```json
{ "correo": "ana@ejemplo.com", "password": "secreto123" }
```

Ambos endpoints devuelven:

```json
{
  "ok": true,
  "data": {
    "usuario": { "id": 1, "nombre": "Ana", "correo": "ana@ejemplo.com" },
    "tokens": {
      "access_token": "...",
      "refresh_token": "...",
      "token_type": "Bearer",
      "expires_in": 3600
    }
  }
}
```

### Enviar el token

En todas las rutas privadas:

```
Authorization: Bearer <access_token>
```

El `access_token` dura una hora (`expires_in`). Cuando la API responda
`TOKEN_EXPIRADO`, renovarlo con:

`POST /api/v1/auth/refresh`

```json
{ "refresh_token": "..." }
```

Devuelve un `access_token` y un `refresh_token` nuevos. El refresh anterior
queda revocado.

### Cerrar sesión

`POST /api/v1/auth/logout` · requiere token. Revoca la sesión de refresco.

### Dispositivo

El ESP32 no usa el token de usuario: usa `X-Device-Token: <token>` en las
rutas `/device/...`. La app usa el token de usuario normal.

## 4. Usuario y perfil

| Método | Ruta | Para qué |
|---|---|---|
| `GET` | `/api/v1/me` | Usuario, perfil, mascota, progreso y puntos |
| `PATCH` | `/api/v1/me` | Editar nombre, presupuesto, zona horaria |
| `GET` | `/api/v1/me/profile` | Perfil financiero |
| `PATCH` | `/api/v1/me/profile` | Editar perfil financiero |
| `GET` | `/api/v1/me/consents` | Consentimientos aceptados |
| `POST` | `/api/v1/me/consents` | Registrar un consentimiento |
| `GET` | `/api/v1/me/wellbeing` | Bienestar de la mascota |

## 5. Home (pantalla principal)

`GET /api/v1/home` · requiere token.

Es la llamada que alimenta la pantalla de inicio. Devuelve todo lo necesario:

```json
{
  "ok": true,
  "data": {
    "usuario": { "id": 1, "nombre": "Ana", "zona_horaria": "America/Bogota" },
    "mascota": { "salud": 100, "animo": "FELIZ", "nombre": "Nancy" },
    "proyeccion_hoy": {},
    "hoy": {
      "ingresos": 0,
      "gastos": 12000,
      "ahorro": 0,
      "balance_neto": -12000,
      "presupuesto_diario": 30000,
      "cupo_restante": 18000,
      "num_registros": 1
    },
    "progreso": {},
    "puntos": 10,
    "fecha_local": "2026-11-04"
  }
}
```

Los montos son enteros en pesos colombianos (no hay centavos).

### Incluir el plan de ahorro

`GET /api/v1/home?incluir_plan=1` agrega `data.plan_ahorro` con un resumen
compacto del plan de metas. Sin la bandera, `/home` no ejecuta el optimizador.

```json
{
  "plan_ahorro": {
    "horizonte_meses": 12,
    "factible": true,
    "solver": "highs",
    "confianza": "media",
    "capacidad_mes_actual": 250000,
    "metas": [
      {
        "meta_id": 3,
        "nombre": "Fondo de emergencia",
        "prioridad": 5,
        "asignacion_mes_actual": 30000,
        "total_asignado": 240000,
        "cumplimiento": 0.44,
        "estado": "parcial",
        "mes_estimado_cumplimiento": null
      }
    ],
    "resumen": { "metas_totales": 1, "cumplimiento_ponderado": 0.44 },
    "diagnostico": {
      "nivel": "info",
      "codigo": "CAPACIDAD_LIMITADA",
      "mensaje": "La capacidad alcanza para el 44 % del plan ponderado."
    }
  }
}
```

El plan solo propone: no modifica metas, transacciones ni saldos.

## 6. Movimientos (voz y texto)

### Enviar una frase de texto

`POST /api/v1/messages` · requiere token · `application/json`

```json
{
  "texto": "gasté 12000 en almuerzo",
  "message_id": "app-1723456789",
  "origen": "app_voz"
}
```

### Enviar audio

`POST /api/v1/messages` · requiere token · `multipart/form-data`

| Campo | Tipo | Obligatorio |
|---|---|---|
| `audio` | archivo WAV | sí |
| `message_id` | texto | sí |
| `idioma` | texto (`es`) | no |
| `origen` | texto (`app_voz`) | no |

Contrato del audio:

- WAV, mono, 16 bits, **16 000 Hz**.
- Entre **0,5 y 40 segundos**.
- Máximo **2 MiB**.
- El backend **no guarda el audio**: solo el texto transcrito y sus metadatos.

`message_id` hace la operación idempotente: si se repite, no se duplica el
movimiento y la respuesta trae `"duplicado": true`.

### Qué devuelve

```json
{
  "ok": true,
  "data": {
    "id": 21,
    "texto_transcrito": "gasté 12000 en almuerzo",
    "transacciones": [
      {
        "id": 22,
        "tipo": "gasto",
        "monto": 12000,
        "concepto": "almuerzo",
        "categoria": "Comida",
        "cuenta": "Nequi",
        "estado": "pendiente",
        "confianza_ia": 0.85
      }
    ],
    "requiere_confirmacion": true
  }
}
```

El contrato conserva estos campos y agrega `mensaje_nancy`, `tipo_respuesta`,
`estado_conversacion`, `datos` y `requiere_confirmacion`. El dispositivo solo
pinta `mensaje_nancy` y el estado; toda la lógica del diálogo vive en el backend.

Una sola frase puede producir **varias transacciones**. `requiere_confirmacion`
indica si hay que mostrar la pantalla de confirmación.

### Confirmar o descartar

| Método | Ruta | Efecto |
|---|---|---|
| `POST` | `/api/v1/messages/{id}/confirm` | Las transacciones pasan a `confirmado` y afectan saldos, puntos y salud |
| `POST` | `/api/v1/messages/{id}/discard` | Se descartan las pendientes |
| `GET` | `/api/v1/messages/{id}` | Consultar el mensaje y sus transacciones |

La confirmación también se responde por voz o texto: "sí", "ok", "correcto",
"está bien" o "confirmo" confirman; "no" o "cancela" descartan. Los endpoints
anteriores llaman a `conversation.invalidar_accion_pendiente` para limpiar el
estado conversacional pendiente del usuario; la siguiente frase vuelve a
empezar su propio turno en vez de tomarse como respuesta a una acción ya
resuelta.

**Regla de negocio: nada afecta el dinero hasta que el usuario confirma.**

### Sintetizar la respuesta en voz

| Método | Ruta | Efecto |
|---|---|---|
| `POST` | `/api/v1/voice/synthesize` | La app recibe la WAV generada en memoria |
| `POST` | `/api/v1/device/voice/synthesize` | El dispositivo recibe la WAV generada en memoria |

La petición lleva:

```json
{ "texto": "Entendí un gasto de veinte mil. ¿Está correcto?" }
```

La respuesta es `Content-Type: audio/wav` con los bytes de la locución. El
backend no guarda el audio en disco ni en la base de datos. Si Piper o el
modelo no están disponibles, responde `503 TTS_NO_DISPONIBLE`. Los textos de
más de 400 caracteres se rechazan con `422 TTS_TEXTO_LARGO`.

Cuando el backend tiene Piper disponible, los mensajes incluyen:

```json
{ "voz": {
  "modo": "online",
  "endpoint": "/api/v1/device/voice/synthesize",
  "idioma": "es_MX"
} }
```

Sin conexión, el dispositivo o simulador puede reproducir un banco pequeño de
frases pregrabadas; no puede sintetizar frases naturales nuevas.

### Transacciones manuales

| Método | Ruta | Para qué |
|---|---|---|
| `GET` | `/api/v1/transactions` | Listar con filtros |
| `POST` | `/api/v1/transactions` | Crear sin pasar por voz |
| `GET` | `/api/v1/transactions/{id}` | Detalle |
| `PATCH` | `/api/v1/transactions/{id}` | Editar |
| `DELETE` | `/api/v1/transactions/{id}` | Mover a la papelera |
| `POST` | `/api/v1/transactions/{id}/restore` | Restaurar |

Filtros de `GET /transactions`: `fecha`, `desde`, `hasta`, `tipo`,
`categoria_id`, `cuenta_id`, `estado`, `incluir_eliminadas`.

## 7. Días, métricas y cierre

| Método | Ruta | Para qué |
|---|---|---|
| `GET` | `/api/v1/days/{YYYY-MM-DD}` | Totales, presupuesto, proyección y desglose por categoría |
| `POST` | `/api/v1/days/{YYYY-MM-DD}/close` | Cerrar el día |
| `GET` | `/api/v1/metrics/daily?fecha=YYYY-MM-DD` | Métricas del día |
| `GET` | `/api/v1/metrics/weekly?fecha=YYYY-MM-DD` | Semana |
| `GET` | `/api/v1/metrics/monthly?fecha=YYYY-MM-DD` | Mes |
| `GET` | `/api/v1/metrics/health` | Salud de la mascota |
| `GET` | `/api/v1/metrics/diagnostics` | Diagnóstico |

## 8. Cuentas, categorías, metas y presupuesto

### Cuentas

| Método | Ruta |
|---|---|
| `GET` | `/api/v1/accounts` |
| `POST` | `/api/v1/accounts` |
| `PATCH` | `/api/v1/accounts/{id}` |
| `DELETE` | `/api/v1/accounts/{id}` |

Tipos válidos: `efectivo`, `billetera_digital`, `tarjeta`,
`cuenta_ahorros`, `inversion`.

### Categorías

| Método | Ruta |
|---|---|
| `GET` | `/api/v1/categories` |
| `POST` | `/api/v1/categories` |
| `PATCH` | `/api/v1/categories/{id}` |
| `POST` | `/api/v1/categories/{id}/deactivate` |

### Metas

| Método | Ruta |
|---|---|
| `GET` | `/api/v1/goals` |
| `POST` | `/api/v1/goals` |
| `GET` | `/api/v1/goals/{id}` |
| `PATCH` | `/api/v1/goals/{id}` |
| `DELETE` | `/api/v1/goals/{id}` |

`prioridad` es un entero entre 1 y 5; la API rechaza valores fuera de rango con
`PRIORIDAD_INVALIDA` (422).

### Plan de metas (Investigación de Operaciones)

| Método | Ruta | Para qué |
|---|---|---|
| `GET` | `/api/v1/goals/plan` | Plan óptimo con los datos reales. |
| `POST` | `/api/v1/goals/plan/simulate` | Probar escenarios sin tocar la base. |

Parámetros de `GET /goals/plan`:

| Parámetro | Default | Rango |
|---|---|---|
| `meses` | 12 | 1–24 |
| `fecha` | hoy en Bogotá | `YYYY-MM-DD` |
| `colchon_pct` | 10 | 0–50 |

Cuerpo de `POST /goals/plan/simulate` (todos opcionales):

```json
{
  "meses": 12,
  "fecha": "2026-11-05",
  "ingreso_mensual": 1500000,
  "gasto_mensual": 800000,
  "colchon_pct": 10,
  "capacidad_mensual": 300000,
  "prioridades": { "3": 5, "4": 2 },
  "incluir_metas": [3, 4]
}
```

Devuelve la misma estructura que `GET` más `simulacion: true` y `overrides`.
Errores: `PARAMETRO_INVALIDO` (422) y `META_INEXISTENTE` (404). El contrato
completo está en `docs/OPTIMIZACION_IO.md`.

### Presupuesto

| Método | Ruta |
|---|---|
| `GET` | `/api/v1/budget` |
| `POST` | `/api/v1/budgets` |
| `POST` | `/api/v1/budgets/{id}/approve` |

## 9. Notificaciones

| Método | Ruta | Para qué |
|---|---|---|
| `GET` | `/api/v1/notifications/settings` | Preferencias |
| `PATCH` | `/api/v1/notifications/settings` | Cambiarlas |

## 10. Dispositivo ESP32

### Vinculación

| Método | Ruta | Token | Para qué |
|---|---|---|---|
| `POST` | `/api/v1/device/register` | ninguno | Registrar un dispositivo nuevo y recibir un PIN de 6 dígitos (vale 10 minutos) |
| `POST` | `/api/v1/device/pair` | usuario | Vincular el dispositivo con `device_uid` y `pin` |
| `GET` | `/api/v1/device` | usuario | Listar dispositivos |
| `POST` | `/api/v1/device/unlink` | usuario | Desvincular |

### Desde el dispositivo

Todas usan `X-Device-Token`.

| Método | Ruta | Para qué |
|---|---|---|
| `POST` | `/api/v1/device/messages` | Enviar audio o texto |
| `POST` | `/api/v1/device/messages/{id}/confirm` | Confirmar |
| `POST` | `/api/v1/device/voice/synthesize` | Sintetizar el texto de respuesta en WAV |
| `POST` | `/api/v1/device/close-day` | Cerrar el día |
| `POST` | `/api/v1/device/telemetry` | Batería, botones, estado |
| `POST` | `/api/v1/finagotchi/telemetry` | Alias antiguo de la telemetría |
| `GET` | `/api/v1/device/notifications` | Recoger notificaciones |
| `POST` | `/api/v1/device/notifications/{id}/ack` | Acusar una |
| `POST` | `/api/v1/device/notifications/ack` | Acusar varias en lote |

El flujo del dispositivo es: **recoger notificaciones → mostrar → acusar**.
La app también puede consultar y confirmar los mensajes del dispositivo con el
token del usuario.

## 11. Errores frecuentes

| Código | HTTP | Qué significa |
|---|---|---|
| `CAMPOS_REQUERIDOS` | 422 | Faltan campos; `detalles.campos` dice cuáles |
| `CREDENCIALES_INVALIDAS` | 401 | Correo o contraseña malos |
| `CORREO_REGISTRADO` | 409 | Ese correo ya existe |
| `PASSWORD_CORTA` | 422 | Menos de 8 caracteres |
| `NO_AUTENTICADO` | 401 | Falta el header `Authorization` |
| `TOKEN_EXPIRADO` | 401 | Renovar con `/auth/refresh` |
| `TOKEN_INVALIDO` | 401 | Token alterado; volver a iniciar sesión |
| `AUDIO_INVALIDO` | 422 | No es WAV o no cumple el formato |
| `AUDIO_MUY_GRANDE` | 413 | Supera 2 MiB o 40 segundos |
| `STT_SIN_TEXTO` | 422 | El audio no tenía voz reconocible |
| `MENSAJE_NO_ENCONTRADO` | 404 | El mensaje no existe o es de otro usuario |
| `DISPOSITIVO_NO_VINCULADO` | 403 | El dispositivo aún no tiene dueño |
| `ERROR_INTERNO` | 500 | Fallo del servidor; revisar la consola |

## 12. Ejemplo completo con `curl.exe`

```powershell
# 1. Registrar
curl.exe -s -X POST http://localhost:5000/api/v1/auth/register `
  -H "Content-Type: application/json" `
  -d '{\"nombre\":\"Ana\",\"correo\":\"ana@ejemplo.com\",\"password\":\"secreto123\"}'

# 2. Iniciar sesion y guardar el token (PowerShell)
$resp = curl.exe -s -X POST http://localhost:5000/api/v1/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"correo\":\"ana@ejemplo.com\",\"password\":\"secreto123\"}' | ConvertFrom-Json
$token = $resp.data.tokens.access_token

# 3. Consultar el home
curl.exe -s http://localhost:5000/api/v1/home -H "Authorization: Bearer $token"

# 4. Enviar una frase
curl.exe -s -X POST http://localhost:5000/api/v1/messages `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{\"texto\":\"gaste 12000 en almuerzo\",\"message_id\":\"demo-1\"}'

# 5. Confirmar el mensaje (usar el id que devolvio el paso 4)
curl.exe -s -X POST http://localhost:5000/api/v1/messages/1/confirm `
  -H "Authorization: Bearer $token"
```

## 13. Notas para quien conecte el frontend

- El frontend actual está limpio: no tiene capa HTTP ni dependencias de red.
  Hay que agregar `http` (y `shared_preferences` si se guardan los tokens) al
  `pubspec.yaml`.
- Guardar `access_token` y `refresh_token`; ante `TOKEN_EXPIRADO`, llamar a
  `/auth/refresh` una vez y reintentar la petición original.
- Para grabar voz se necesita un formato que el backend acepte: WAV PCM 16 kHz
  mono 16 bits. En web el micrófono del navegador entrega webm/opus, que no
  sirve; en web conviene ofrecer la entrada por texto.
- Los montos viajan como enteros. No usar decimales.
- La confirmación humana es obligatoria: nunca confirmar automáticamente.
