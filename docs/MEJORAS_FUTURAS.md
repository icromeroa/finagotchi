# Mejoras futuras de FinaGotchi

> Este documento solo acumula ideas. Nada de aquí se implementa hasta que se priorice.
> El plan de firmware actual es push-to-talk con botón; la wake word queda para después.

## Voz (wake word)

- [ ] Wake word offline “Nancy” (ESP-SR / Sherpa-ONNX) con PSRAM confirmada.
- [ ] Medir falsos positivos (TV, otra persona) y falsos negativos en español coloquial.
- [ ] Evaluación de batería: micrófono siempre activo vs push-to-talk.
- [ ] Alternativa: wake word en backend si se acepta latencia y costo.
- [ ] AFE: supresión de ruido para pedir montos como “20 mil”.

## Interacción

- [ ] Flujo push-to-talk con los 3 botones: hablar / confirmar / cancelar.
- [ ] Indicador visual en TFT 240×320 del estado (escuchando / pensando / confirmado).
- [ ] Fluidez con resoluciones 240×320 y tipografía legible a distancia (referencia Troko, sin copiar su layout 240×240).

## Hardware portable

- [ ] Board propia ESP-IDF 6.1 con pines TFT/batería/botones propios (Troko solo como referencia de I2S).
- [ ] Batería 18650 con BMS, carga USB-C y autonomía medida.
- [ ] Caja, protección eléctrica y certificación según uso.

## Backend e IA

- [ ] Nivel de confianza de la transcripción para fechas y montos (“ayer”, “del 3 al 5”).
- [ ] Glosario de categorías en español para mejorar el STT (“alimentación”, “transporte”).
- [ ] Métricas: latencia STT→TTS y WER en frases financieras.

## Privacidad y producción

- [ ] TLS, tokens rotables (`device_token`) y retención mínima de audio.
- [ ] Provisionamiento en fábrica (sin `config.local.json` manual) y OTA firmada.
- [ ] Backend en infraestructura propia con alta disponibilidad.
