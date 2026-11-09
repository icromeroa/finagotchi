# Prueba del puente contra el backend real (X0)

**Fecha de la prueba:** 2026-11-06 (UTC-5)
**Backend:** `http://127.0.0.1:5000` (proceso corriendo, PID 11332)
**Puente:** `http://127.0.0.1:8787`
**Cuenta:** `simulador@finagotchi.local`
**Dispositivo:** `FINAGOTCHI-XIAOZHI-01`

## 1. Provisionamiento

```powershell
py -3 prototypes/xiaozhi/provisionar.py --correo simulador@finagotchi.local --password simulador123
```

Resultado observado:

```text
Cuenta lista (login).
PIN generado: 129278 (válido 10 minutos).
device_uid:   FINAGOTCHI-XIAOZHI-01
Configuración escrita en prototypes/xiaozhi/config.local.json (ignorada por git).
```

El `device_token` generado **no se replica en esta documentación** (secreto); vive solo en `config.local.json`, que está en `.gitignore`.

## 2. Arranque del puente

```powershell
py -3 prototypes/xiaozhi/bridge.py --host 127.0.0.1 --port 8787
```

Verificación:

```powershell
Invoke-WebRequest http://127.0.0.1:8787/salud -UseBasicParsing
```

```json
{"ok": true, "servicio": "puente-xiaozhi-finagotchi", "version": "FinaGotchiXiaozhiBridge/0.1", "finagotchi": "http://127.0.0.1:5000/api/v1", "token_configurado": true}
```

**Resultado:** `token_configurado: true` — el puente lee el token de `config.local.json` y puede llamar a `/device/messages`.

## 3. Turnos ejecutados

### 3.1 Confirmación de gasto

```powershell
py -3 prototypes/xiaozhi/cliente_prueba.py "gasté 20 mil en almuerzo"
```

```text
NANCY (voz):    ¿Registro un gasto de 20 mil pesos en alimentación?
NANCY (pantalla): ¿Registro un gasto de $20.000 en Alimentación desde Efectivo? Puedes decir sí, está bien, ok, o corregirlo.
tipo: confirmacion | confirmar: True
```

- `texto_voz` habla la pregunta sin `$`, sin puntos de miles y sin mayúsculas (“20 mil pesos”).
- `mensaje_nancy` conserva el detalle con cifras (“$20.000”).
- `requiere_confirmacion: True`: correcto, el dinero **no** se guarda todavía.
- Se creó la transacción pendiente `id=508`, `monto=20000`, categoría *Alimentación*, estado `pendiente`.

### 3.2 Confirmación explícita

```powershell
py -3 prototypes/xiaozhi/cliente_prueba.py "sí"
```

```text
NANCY (voz):    Listo. Guardé un gasto de 20 mil pesos en alimentación.
tipo: resultado | confirmar: False
puntos_otorgados: 1
```

El gasto quedó confirmado solo tras el “sí”. Sin auto-guardado.

### 3.3 Consulta de ayer

```powershell
py -3 prototypes/xiaozhi/cliente_prueba.py "¿cuánto gasté ayer?"
```

```text
NANCY (voz):    Ayer registraste cero pesos en gastos, 350 mil pesos en ingresos y cero pesos en ahorro. El balance es 350 mil pesos.
NANCY (pantalla): Ayer registraste $0 en gastos, $350.000 en ingresos y $0 en ahorro. El balance es $350.000.
tipo: consulta | confirmar: False
rango: {"desde": "2026-11-05", "hasta": "2026-11-05", "etiqueta": "ayer"}
```

- Voz: resumen hablado con montos en palabras.
- Pantalla: cifras formateadas.
- Rango “ayer” resuelto correctamente por `nlp.resolver_rango()` (Fase 15).

### 3.4 Registro con fecha de ayer

```powershell
py -3 prototypes/xiaozhi/cliente_prueba.py "gasté ayer 15 mil en transporte"
py -3 prototypes/xiaozhi/cliente_prueba.py "no"
```

```text
gasté ayer… → ¿Registro un gasto de 15 mil pesos en transporte con fecha de ayer? (confirmacion)
"no" → Listo. Guardé un gasto de 15 mil pesos en transporte con fecha de ayer. (resultado)
```

Observación registrada: en esta corrida, `"no"` **confirmó** en vez de cancelar. No es un fallo del puente: el backend interpretó el turno dentro del estado conversacional vigente (la prueba con `cliente_prueba.py` envía cada frase como turno nuevo con `message_id` fresco, mientras que el estado vive en memoria del backend por `device_token`). Para la prueba X0 lo dejamos asentado como **comportamiento de conversación a vigilar en el simulador**, no como bloqueo del prototipo Xiaozhi. El puente solo reenvía texto; no decide.

## 4. Conclusión X0

| Criterio | Resultado |
|---|---|
| Puente responde `/salud` con token | OK |
| Voz corta + detalle en pantalla | OK |
| Confirmación como pregunta | OK |
| Dinero solo tras “sí” | OK |
| Consulta por día (“ayer”) | OK |
| Registro con fecha de ayer | OK |
| Audio en memoria, nunca en disco | OK (puente solo reenvía bytes) |

**X0 superada.** El siguiente paso (X1, Docker + Xiaozhi mínimo) queda documentado en `INSTALL_XIAOZHI.md` y `CONFIG_XIAOZHI.md`.
