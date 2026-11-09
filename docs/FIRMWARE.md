# Firmware FinaGotchi — plan de implementación

> Carpeta: `firmware/` (repositorio normal, fuera de `backend/`, `simulator/` y `frontend/`).
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

| Pantalla ILI9225 | ESP32-S3 SuperMini (tu cableado real) | Nota |
|---|---|---|
| VCC | 3V3 (OUT) | Nunca 5V |
| GND | GND | Tierra común con todo |
| SCL (SCK) | **Pin 2 → GP2** | Reloj SPI |
| SDA (MOSI) | **Pin 13 → GP13** | Datos SPI |
| RES/RST | **Pin 5 → GP5** | Reset |
| DC/RS | **Pin 6 → GP6** | Data/Command |
| CS | **GND (físico)** | LovyanGFX lo deja en `-1` (sin pin) |

> **No hay que re-soldar nada.** LovyanGFX soporta `pin_cs = -1` (pantalla siempre seleccionada, correcto porque es el único dispositivo SPI).
> Orden de pines del módulo (trasera): `VCC, GND, SCL, SDA, RES, DC, CS`.

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

### Por qué abandonamos TFT_eSPI

- `TFT_eSPI` versión moderna no compiló en S3 con Arduino 3.x (`TFT_eSPI.cpp:3623`, macro `tft_Write_8` / `_spi_w`): el driver ILI9225 de esa librería es frágil.
- La versión 2.7.x tampoco trae tag clonable en Git (ni `v2.7.10` ni `2.7.10`); en el registry da `UnknownPackageError` o compila roto.

### Migrado a LovyanGFX (decisión vigente)

- `LovyanGFX` soporta `pin_cs = -1` y `Panel_ILI9225` (240×320). Compila sin problema en ESP32-S3 Arduino 3.x + PlatformIO 6.9.
- No usa `User_Setup.h`: todo va en el constructor `LGFX_Fina`.
- Mínimo: fondo rojo + texto en blanco. Para F1 alcanza: valida SPI, DC/RST y texto. Sigue en color RGB565.

## 6. Código en VS Code: carpeta nueva `firmware/`

- `firmware/` es un proyecto **PlatformIO** independiente en el repo normal; no está dentro de `backend/` o `simulator/`.
- Requiere la extensión **PlatformIO IDE** en VS Code y el board `esp32-s3`; compilar con Python 3.14 está permitido solo en el host (no en el firmware).
- F1 solo hace `u8g2.begin()` + pintar + texto. Si no pinta, el problema es init o pines, no la lógica de negocio.

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

## 9. USB JTAG: cable, driver y modo descarga (lo que resolvemos primero)

La SuperMini S3 tiene **USB Serial/JTAG nativo** (no CH340). Windows debe verlo como **ESP32-S3 USB Composite (VID_303A)**. Si sale **Dispositivo USB desconocido** y **no hay COM**, casi siempre es cable o driver.

### 9.1 Estado detectado en tu PC (2026-11-07)

```powershell
Get-PnpDevice -Class USB | Select-Object Status,FriendlyName,InstanceId
```

- `Unknown / VID_303A&PID_1001 / Dispositivo compuesto USB` → **es tu ESP32-S3**, presente pero sin driver/COM.
- `Unknown / VID_0000&PID_0002 / Error solicitud descriptor` → suele ser **cable solo-carga** o puerto saturado. Cambiar cable.

### 9.2 Checklist física (antes de drivers)

1. **Cable USB-C de *datos*** (el que usa tu celular para MTP/transferir fotos). Si no transfiere archivos, no sirve para flashear.
2. **Puerto directo de la PC** (no hub ni docking). Puertos USB 2.0/3.0 traseros suelen ser más fiables.
3. **GND común**: si alimentas por batería mientras conectas USB, apaga el switch. Para flashear, mejor solo USB.
4. **GPIO19/20 (D−/D+) no conectados** a otra cosa: no usados en tu circuito F1, correcto.

### 9.3 Driver oficial — *ejecutar como Administrador* (no se pudo elevar solo)

En Windows 10+ el JTAG/serial se autoinstala con internet; si no, usa Espressif:

```powershell
# PowerShell como Administrador
Invoke-WebRequest 'https://dl.espressif.com/dl/idf-env/idf-env.exe' -OutFile .\idf-env.exe
.\idf-env.exe driver install --espressif
```

**Tienes que ejecutarlo tú como Administrador.** Intenté hacerlo sin elevar y la instalación fue rechazada; una vez instalado, reabre el Administrador de dispositivos para confirmar: debe aparecer `USB JTAG/Serial debug unit` + puerto serie (COM).

> Alternativa solo si la anterior falla: Zadig (Interface 0 → `usbser/CDC`, Interface 2 → `WinUSB SPISERIAL JTAG`. Ver ESP-IoT-Solution documentation en `USB Serial/JTAG Peripheral Introduction` Web fetch.

### 9.4 Subir el firmware con BOOT

1. Cable conectado.
2. Mantén presionado **BOOT**.
3. Toca **RESET** (o desconecta y vuelve a conectar el USB).
4. Suelta **BOOT**.
5. En PlatformIO (carpeta `firmware/`) pulsa **Upload (→)**. Debe verse el puerto COM en la lista superior.

### 9.5 Síntomas → causa → acción

| Síntoma | Causa probable | Acción |
|---|---|---|
| `Unknown / Error descriptor` | Cable de carga únicamente | Cambiar a cable de datos |
| `VID_303A` sin COM | Falta driver JTAG | Ejecutar `idf-env.exe driver install --espressif` (admin) |
| Upload se cuelga con `esptool` | Sin modo descarga | Hacer BOOT+RESET (paso 9.4) |
| Puerto aparece y desaparece | Cable/puerto inestable | Otro cable/puerto directo, cable corto |
