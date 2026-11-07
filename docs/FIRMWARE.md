# Firmware FinaGotchi — plan de implementación

> Carpeta: `firmware/` (repositorio normal, fuera de `prototypes/xiaozhi/`, `backend/`, `simulator/` y `frontend/`).
> Estado: **F1 — pantalla ILI9225 en prueba**. Decisión vigente: push-to-talk ahora; wake word en `docs/MEJORAS_FUTURAS.md`.

## 1. Hardware objetivo (verificado por fotos y plano)

| Componente | Detalle confirmado |
|---|---|
| ESP32-S3 SuperMini | 11 GPIO, 16 MB Flash, PSRAM confirmada; pines rotulados en el plano adjunto |
| Pantalla | GMT024-10 v2.1, 2.4", 240×320, controlador **ILI9225**, 7 pines (VCC/GND/SCL/SDA/RES/DC/CS), sin BLK |
| Micrófono | INMP441 digital I2S |
| Amplificador | MAX98357A I2S (anotado “12S” en la lista; es I2S) |
| Altavoz | 8 Ω, 0.5 W |
| Botones | 3 pulsadores |
| Batería | 18650 + BMS/cargador + portapila + switch |
| Cables/protoboard | Jumpers, tierra común (GND) obligatoria |

## 2. Pines reales (desde tu foto, no los números de borde)

Los números del borde de la SuperMini **no son GPIO**. La tabla correcta, según el plano que pegaste:

- **Lado alto (USB):** `GP1, GP2, GP3, GP4, GP5, GP6, GP7` (izquierda) y `GP8, GP9, GP10, GP11, GP12, GP13` (derecha), más `TX/RX` y `3V3/GND/5V/BAT`.
- **Lado bajo:** `GP14, GP15, GP16, GP17, GP18, GP21, GP33, GP34, GP37, GP38` (izquierda) y `GP39, GP40, GP41, GP42, GP45, GP46, GP47, GP48, GP35, GP36` (derecha), `TX/RX`, `B+/B-`, `5V/GND/3V3`.

> `GP48` es el RGB WS2818/I LED azul de la placa: **no usar** para pantalla ni audio. `GP33–GP38, GP45–GP48` son limitados en variantes N16R8 (octal PSRAM/flash) y strapping: **evitarlos** en este proyecto. Se usan solo pines seguros.

## 3. Tabla de conexión propuesta (F1 = solo pantalla)

Tu cableado anterior (CS a GND, Pin 2/13/5/6 genéricos) se corrige así:

| Pantalla ILI9225 | ESP32-S3 SuperMini | Nota |
|---|---|---|
| VCC | 3V3 | Nunca 5V |
| GND | GND (riel común) | Tierra común obligatoria |
| SCL (SCK) | **GP12** | SPI clock |
| SDA (MOSI) | **GP11** | SPI data |
| RES/RST | **GP9** | Reset físico |
| DC/RS | **GP10** | Data/Command |
| CS | **GP13** → luego GND si funciona | Primero como GPIO; si se atora, bajar a GND |

> Cables cortos (CLK/DATA). Conexión en orden de pines del módulo: `VCC, GND, SCL, SDA, RES, DC, CS` (ver foto trasera, serigrafía `GND VCC SCK SDA RST DC CS`).

## 4. Tabla propuesta para audio/botones (F2, no cablear aún en F1)

| Uso | GPIO | Nota |
|---|---|---|
| INMP441 SCK | GP15 | I2S |
| INMP441 WS | GP16 | |
| INMP441 SD | GP17 | LR a GND |
| MAX98357A BCLK | GP18 | I2S |
| MAX98357A LRC | GP21 | |
| MAX98357A DIN | GP14 | SD_MODE a 3.3V o libre (nunca a GND: apaga el amp) |
| Botón 1 (hablar) | GP1 | Pull-up interno, GND |
| Botón 2 (sí/confirmar) | GP2 | |
| Botón 3 (no/cancelar) | GP3 | |
| LED RGB de placa | GP48 | No tocar: diagnóstico con LED azul propio |

## 5. ¿Por qué la pantalla quedó blanca?

Es el controlador. La ILI9225 necesita su propia secuencia de init (configuración de 240×320, 18 bits/píxel). Si inicializas ILI9341 o ST7789, la pantalla se enciende (backlight sin BLK siempre a 3.3V) pero **nunca forma la imagen**.

### Qué es `User_Setup.h`

Es un archivo **dentro** de la librería `TFT_eSPI` que le dice 3 cosas: qué pantalla (`ILI9225_DRIVER`), qué GPIO son `TFT_MOSI/SCLK/CS/DC/RST`, y qué tamaño (240×320). Sin editarlo, la librería carga otro controlador y tu panel no reacciona.

En este proyecto no editamos el `User_Setup.h` global de la librería; usamos `User_Setup.h` y `User_Setup_Select.h` **dentro de `firmware/`** para no romper otras instalaciones.

## 6. Código en VS Code: carpeta nueva `firmware/`

- `firmware/` es un proyecto **PlatformIO** independiente en el repo normal; no está dentro de `prototypes/xiaozhi/` ni de `backend/` o `simulator/`.
- Requiere la extensión **PlatformIO IDE** en VS Code y el board `esp32-s3`; compilar con Python 3.14 está permitido solo en el host (no en el firmware).
- F1 solo hace `display.init()` + pintar rojo/texto. Si no pinta, el problema es init o pines, no la lógica de negocio.

## 7. Plan por fases

- **F1:** pantalla ILI9225 roja con texto “FinaGotchi” (sin mic, sin red).
- **F2:** I2S mic + amp (eco de prueba local) + botones; medir pico/RMS como el simulador.
- **F3:** red: `POST /device/messages` y `POST /device/voice/synthesize` (mismo contrato que el puente).
- **F4:** pantallas D01/D04/D06/D07 según `docs/DISPOSITIVO.md` y estados de Nancy.
- **F5+:** producción (carcasa, batería, OTA). Wake word solo en `docs/MEJORAS_FUTURAS.md`.

## 8. Reglas de seguridad eléctrica (de tu tabla, confirmadas)

- Batería 18650 → BMS (B+/B−) → switch → 5V de la placa. Nunca a 3V3 directo.
- VCC de pantalla y mic a **3.3V**; `VIN` del amp a **5V**.
- `SD`/`GAIN` del MAX98357A libres o a 3.3V; **nunca a GND**.
- Tierra común en el riel GND de la protoboard para todos los módulos.
- Cables cortos en bus SPI; soldadura recomendada antes de producción.
