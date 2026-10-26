# FinaGotchi

Asistente financiero IoT por voz: el usuario habla ("gasté 14000 en el almuerzo"), el simulador transcribe y envía la lectura al backend, que la guarda en SQLite y actualiza la salud de la mascota.

**Integrantes:** Helen Andrea Lavao Benitez · Danna Michelle Guzman Angarita · Irene Charlotte Romero Avendaño
**Asignatura:** Desarrollo de Aplicaciones AV - Universidad de San Buenaventura

## Arquitectura

```
Simulador (voz) --POST /api/v1/finagotchi/telemetry--> Backend Flask --> SQLite (finagotchi.db)
                                                            ^
Swagger (/docs) / futuro dashboard --GET /api/measurements | /api/devices
```

## Instalación

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Ejecutar

```bash
python3 backend/server.py                     # Terminal 1 -> http://127.0.0.1:8000
sudo python3 simulator/simulator.py           # Terminal 2 (voz; macOS pide sudo por la librería keyboard)
python3 simulator/enviar_lecturas.py --n 10   # alternativa sin micrófono
```

Swagger: http://127.0.0.1:8000/docs

## Endpoints

| Método | Ruta | Propósito |
|---|---|---|
| POST | `/api/v1/finagotchi/telemetry` | Recibir lectura del simulador |
| GET | `/health` | Estado del servicio |
| GET | `/api/measurements?device_id=&limit=20&offset=0` | Histórico (limit 1-100) |
| GET | `/api/devices` | Dispositivos detectados |
| GET | `/api/devices/{device_id}` | Resumen de un dispositivo (404 si no existe) |

## Ejemplos

```bash
curl -s "http://127.0.0.1:8000/api/measurements?limit=5"
curl -s "http://127.0.0.1:8000/api/measurements?device_id=FINAGOTCHI-PC-SIMULATOR-01&limit=10&offset=0"
curl -i  "http://127.0.0.1:8000/api/devices/NO-EXISTE"      # 404
curl -i  "http://127.0.0.1:8000/api/measurements?limit=500"  # 422
```

## Pruebas

```bash
python3 -m pytest -q                    # automáticas (base temporal)
python3 tests/probar_api_manual.py      # matriz manual (backend encendido)
```

## Estado y pendientes

Listo: POST de telemetría, GET de mediciones y dispositivos, filtros, paginación, Swagger, pruebas.
Pendiente: filtro `from`/`to` y dashboard. Ver [PROBLEMAS_CONOCIDOS.md](PROBLEMAS_CONOCIDOS.md).
Diseño de la API: [docs/decisiones/api-rest.md](docs/decisiones/api-rest.md).
