# Hacia un dispositivo portable de producción

> Este documento marca la distancia entre el prototipo actual y el producto final. **No se toma ninguna decisión de producción aquí**; solo se deja trazado qué faltará.

## 1. Dónde estamos hoy

| Capa | Hoy (prototipo) | Producción (meta) |
|---|---|---|
| Hardware | ESP32-S3 SuperMini 16 MB, PSRAM confirmada, TFT 240x320, 3 botones, INMP441, MAX98357A, 18650 | Mismo núcleo con board propia, caja, protecciones y certificación |
| Firmware | Ninguno (fuera de alcance) | ESP-IDF 6.x custom (pines TFT/botones/batería) |
| Wake word | Por defecto en chino | “Nancy” local (AFE + KWS offline) |
| STT | Whisper API (Groq/OpenAI) | Evaluación offline vs API según costo/latencia |
| LLM | Groq/Zhipu cloud con `function_call` | Costo, latencia y privacidad evaluadas; posible destilación local |
| TTS | `EdgeTTS` → Piper `es-MX` en backend | Empaquetado local y fallback offline |
| Backend | PC local `5000` | Infraestructura propia con TLS y alta disponibilidad |
| Emparejamiento | `device_token` manual (`config.local.json`) | Provisionamiento en fábrica / QR / BLE |

## 2. Riesgos de producción

1. **Dependencia de red:** STT/LLM/TTS remotos → latencia y caída. Medir antes de prometer offline.
2. **Privacidad financiera:** los gastos son datos sensibles. En producción: TLS extremo a extremo, tokens rotables y retención mínima.
3. **Costo por turno:** Whisper + LLM + TTS por cada frase. Estimar costo mensual por usuario antes de escalar.
4. **Idioma:** Whisper en español rioplatense/coloquial: medir tasa de error en “ayer”, “anteayer”, “del 3 al 5”.
5. **Batería/carga:** 18650 con protección, carga USB-C y autonomía medida.
6. **Pantalla:** TFT 240x320 no es una placa típica Xiaozhi: requerirá board custom en el firmware.

## 3. Puertas de decisión (nada automático)

1. ¿Xiaozhi reemplaza el firmware propio o solo aporta wake word + AFE?
2. ¿STT offline (Vosk/Whisper local) o API?
3. ¿LLM cloud o modelo destilado local?
4. ¿Backend en la nube propia o en LAN del usuario?

## 4. Lo que no se hace ahora

- Flashear la placa con el `.bin` oficial (no maneja nuestro TFT ni pines).
- Subir el `device_token` a Git o a la nube oficial.
- Reescribir el backend: sigue siendo la fuente de verdad.

## 5. Checklist de producción (futura)

- [ ] Wake word “Nancy” medida en ambiente con ruido
- [ ] Board custom ESP-IDF (TFT, botones, batería, carga)
- [ ] Provisionamiento sin intervenir `config.local.json`
- [ ] TLS + tokens rotables + OTA firmada
- [ ] Métricas: latencia STT→TTS, tasa de error WER en español, costo por turno
- [ ] Caja, certificación eléctrica y prueba de caída/agua según uso
