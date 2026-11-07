# Firmware FinaGotchi (fuera de prototypes/xiaozhi/)

> Carpeta `firmware/` del repo normal. No toca `backend/`, `simulator/`, `frontend/` ni `prototypes/xiaozhi/`.
> Ver especificaciones de hardware y pines en `docs/FIRMWARE.md`.

## Estructura

```text
firmware/
├── platformio.ini   # Board esp32-s3, ILI9225 240x320, pines reales
├── README.md
└── src/
    └── main.cpp    # F1: solo pantalla ILI9225 (rectángulo rojo + texto)
```

`.pio/` (build interno de PlatformIO) está ignorado por Git vía `firmware/.gitignore`.

## Ruta recomendada (VS Code)

1. Instalar la extensión **PlatformIO IDE**.
2. Abrir la carpeta `firmware/` en VS Code.
3. Pulsar **Build** (✓ en la barra inferior o icono pio en la izquierda) → esperar `SUCCESS`, señal de que bajó el framework y `TFT_eSPI`.
4. Cable USB-C **de datos** al PC (directo, sin hub). Si Windows dice *“Dispositivo USB desconocido”*, instala el driver Espressif USB-Serial-JTAG (§9 en `docs/FIRMWARE.md`). Recuerda que `firmware/src/main.cpp` solo pinta la pantalla, no lo que más vale para el proyecto.

## Conexión F1 (solo pantalla)

| Pantalla | ESP32-S3 |
|---|---|
| VCC | 3V3 (OUT) |
| GND | GND |
| SCL (SCK) | **Pin 2 → GP2** |
| SDA (MOSI) | **Pin 13 → GP13** |
| RES | **Pin 5 → GP5** |
| DC | **Pin 6 → GP6** |
| CS | **GND (físico)** → LovyanGFX `pin_cs=-1` |

> Cables cortos en SCL/SDA. VCC nunca a 5V. Con LovyanGFX, CS puede quedar a GND (sin pin): la pantalla es el único dispositivo SPI.

## F1: qué esperar (LovyanGFX)

- Al arrancar, la pantalla pasa de blanca a roja con “FinaGotchi / ILI9225 OK”.
- Serial (115200) muestra `FinaGotchi F1 (LovyanGFX): pintura completada`.
- Si sigue blanca: revisa `DC/RST`, cables cortos y prueba SPI a 5 MHz (`freq_write=5000000`).

## F2 (no implementada)

Micrófono INMP441, amplificador MAX98357A y 3 botones según la tabla en `docs/FIRMWARE.md` (§4).

## Licencias y referencia

- Controlador ILI9225 y librería `LovyanGFX` (LGPL 3.0). Documentado solo para uso con el módulo GMT024-10 v2.1.
- **Motivo:** `TFT_eSPI` no compiló en S3 Arduino 3.x. U8g2 tampoco permite `CS=-1`; LovyanGFX sí, con tu cableado intacto.
- Troko (MIT) se cita solo como referencia de flujo; no se copió su firmware ni su tabla de pines.
