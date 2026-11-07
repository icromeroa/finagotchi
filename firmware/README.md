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
| CS | **Pin 7 → GP7** (mover desde GND) |

> Cables cortos en SCL/SDA. VCC nunca a 5V. Con U8g2, CS debe ser GPIO: dejarlo en GND causaría cortocircuito cuando el driver lo pone en alto.

## F1: qué esperar (U8g2)

- Al arrancar, la pantalla rellena en blanco con texto negro “FinaGotchi / ILI9225 OK”.
- Serial (115200) muestra `FinaGotchi F1 (U8g2): pintura completada`.
- Si sigue blanca: revísa `CS` (GP7, no GND), `RST/DC` y prueba SPI a 5 MHz (`setBusClock(5000000)`).

## F2 (no implementada)

Micrófono INMP441, amplificador MAX98357A y 3 botones según la tabla en `docs/FIRMWARE.md` (§4).

## Licencias y referencia

- Controlador ILI9225 y librería `U8g2` (BSD). Documentado solo para uso con el módulo GMT024-10 v2.1.
- **Motivo:** `TFT_eSPI` no compiló en S3 Arduino 3.x (error interno `tft_Write_8`); U8g2 sí trae driver ILI9225 estable.
- Troko (MIT) se cita solo como referencia de flujo; no se copió su firmware ni su tabla de pines.
