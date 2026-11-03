# Simulador FinaGotchi (PC)

El simulador representa el dispositivo físico: inicia sesión con un usuario de prueba, vincula un dispositivo virtual, captura voz, envía el texto al backend y confirma el registro propuesto.

> **Cambio pendiente:** el flujo objetivo es que el simulador envíe audio a `POST /api/v1/device/messages` y que la IA del backend haga la transcripción y la clasificación. El endpoint ya existe, pero mientras no haya proveedor STT configurado el simulador transcribe en el PC con Google Speech Recognition y envía `texto` como fallback.

## Requisitos

- Python 3.10 o superior.
- Micrófono.
- Conexión a Internet para Google Speech Recognition.
- Backend v2 iniciado.
- Permisos de administrador para que `keyboard` capture la tecla ESPACIO.

## Instalación

```powershell
py -3 -m pip install flask requests keyboard SpeechRecognition sounddevice scipy numpy
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
  "language": "es-CO"
}
```

- `auto_confirm: true` guarda las propuestas sin pedir confirmación.
- `auto_confirm: false` muestra la propuesta y pide `[S/n]`.
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

Mantén presionada la tecla ESPACIO mientras hablas. Al soltarla, el simulador transcribe y envía el texto al dispositivo virtual.

## Frases de prueba

Gastos:

- "Gasté 12.000 en el almuerzo"
- "Pagué 8.000 de transporte"
- "Compré un café por 5 mil"

Ingresos:

- "Me pagaron 50.000 por un trabajo"
- "Recibí 20.000 de mesada"

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
5. `POST /device/messages` con el texto transcrito.
6. Si hay una propuesta, `POST /device/messages/{id}/confirm`.
7. Tras confirmar, `GET /device/notifications?after_id=N` cada 3–5 segundos y `POST /device/notifications/{id}/ack`.
8. Para cierre, `POST /device/close-day`.
9. Para consultas, `GET /home`.

El simulador envía `texto`, `message_id` y `audio_duracion_s`. El backend crea transacciones en estado `pendiente`; solo la confirmación las vuelve `confirmado`, otorga puntos y afecta el saldo. La confirmación de un mensaje originado en el dispositivo crea una notificación `movimiento_registrado` que el simulador puede consultar por polling.

## Problemas frecuentes

- `ERROR DE CONEXIÓN`: verifica que el backend escuche en `http://127.0.0.1:5000`.
- `401` o `403`: el dispositivo está vinculado a otra cuenta; usa otro `device_uid` o desvincula el dispositivo desde la app.
- `keyboard` no detecta ESPACIO: ejecuta la terminal como administrador.
- No hay transcripción: revisa el micrófono, la conexión a Internet y el idioma `es-CO`.
- El backend no arranca: verifica `py -3 database/init_db.py` y que `finagotchi.db` no sea una base legacy.
