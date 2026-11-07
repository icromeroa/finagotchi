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
3. Pulsar **Build** (marcador de verificación) para compilar sin conectar la placa.
4. Conectar la ESP32-S3 SuperMini por USB-C y pulsar **Upload** (flecha a la derecha).

## Conexión F1 (solo pantalla)

| Pantalla | ESP32-S3 |
|---|---|
| VCC | 3V3 (OUT) |
| GND | GND |
| SCL (SCK) | **Pin 2 → GP2** |
| SDA (MOSI) | **Pin 13 → GP13** |
| RES | **Pin 5 → GP5** |
| DC | **Pin 6 → GP6** |
| CS | **GND (físico)** → código `TFT_CS=-1` |

> Cables cortos en SCL/SDA. VCC nunca a 5V. Compilar con el controlador **ILI9225**: otro controlador deja la pantalla blanca aunque esté bien conectada.

## F1: qué esperar

- Al arrancar, la pantalla pasa de blanca a roja con “FinaGotchi / ILI9225 OK”.
- Serial (115200) muestra `FinaGotchi F1: pintura completada`.
- Si sigue blanca: orden `CS a GND` (desconectar GP13), revisar `RST/DC` y probar SPI a 10 MHz.

## F2 (no implementada)

Micrófono INMP441, amplificador MAX98357A y 3 botones según la tabla en `docs/FIRMWARE.md` (§4).

## Licencias y referencia

- Controlador ILI9225 y librería `TFT_eSPI` (GPL). Documentado solo para uso con el módulo GMT024-10 v2.1.
- Troko (MIT) se cita solo como referencia de flujo; no se copió su firmware ni su tabla de pines.
