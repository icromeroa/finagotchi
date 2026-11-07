/**
 * FinaGotchi — Firmware F1 (prueba mínima de pantalla ILI9225 con LovyanGFX)
 *
 * Objetivo: salir de la pantalla blanca. Solo inicializa la pantalla
 * ILI9225 (240x320) con LovyanGFX y pinta fondo + texto "FinaGotchi".
 * Sin micrófono, sin red, sin botones.
 *
 * Conexión final (ver docs/FIRMWARE.md) — SIN RE-SOLDAR NADA:
 *   VCC  -> 3V3
 *   GND  -> GND
 *   SCL (SCK) Pin 2  -> GP2
 *   SDA (MOSI) Pin 13 -> GP13
 *   RES (RST) Pin 5  -> GP5
 *   DC Pin 6         -> GP6
 *   CS -> GND (físico): en LovyanGFX se deja en -1 (sin pin), así no
 *        se cortocircuita y la pantalla queda siempre seleccionada,
 *        que es lo correcto porque es el único dispositivo SPI.
 */

#include <Arduino.h>

#define LGFX_USE_V1
#include <LovyanGFX.hpp>

#define LGFX_MOSI_PIN 13  // GP13 (Pin 13)
#define LGFX_SCLK_PIN 2   // GP2  (Pin 2)
#define LGFX_DC_PIN 6     // GP6  (Pin 6)
#define LGFX_RST_PIN 5    // GP5  (Pin 5)

class LGFX_Fina : public lgfx::LGFX_Device
{
    lgfx::Panel_ILI9225 _panel;
    lgfx::Bus_SPI _bus;

public:
    LGFX_Fina(void)
    {
        // Bus SPI
        {
            auto cfg = _bus.config();
            cfg.spi_host = SPI2_HOST;          // ESP32-S3: VSPI_HOST está deprecado
            cfg.spi_mode = 0;
            cfg.freq_write = 10000000;         // 10 MHz a prueba para ILI9225
            cfg.freq_read = 10000000;
            cfg.spi_3wire = false;
            cfg.use_lock = true;
            cfg.dma_channel = SPI_DMA_CH_AUTO;
            cfg.pin_sclk = LGFX_SCLK_PIN;
            cfg.pin_mosi = LGFX_MOSI_PIN;
            cfg.pin_miso = -1;                 // sin MISO
            cfg.pin_dc = LGFX_DC_PIN;
            _bus.config(cfg);
            _panel.setBus(&_bus);
        }
        // Panel ILI9225
        {
            auto cfg = _panel.config();
            cfg.pin_cs = -1;                   // CS a GND (sin pin)
            cfg.pin_rst = LGFX_RST_PIN;
            cfg.pin_busy = -1;
            cfg.panel_width = 240;             // ancho real
            cfg.panel_height = 320;            // alto real
            cfg.offset_x = 0;
            cfg.offset_y = 0;
            cfg.offset_rotation = 0;
            cfg.dummy_read_pixel = 8;
            cfg.dummy_read_bits = 1;
            cfg.readable = false;              // ILI9225: no leer de vuelta
            cfg.invert = false;
            cfg.rgb_order = false;
            cfg.dlen_16bit = true;             // ILI9225 envía 16-bit
            cfg.bus_shared = false;
            _panel.config(cfg);
        }
        setPanel(&_panel);
    }
};

static LGFX_Fina lcd;

void setup()
{
    Serial.begin(115200);
    delay(100);
    Serial.println("FinaGotchi F1 (LovyanGFX): iniciando pantalla ILI9225 240x320");
    Serial.println("MOSI=GP13 SCLK=GP2 CS=GND(-1) DC=GP6 RST=GP5");

    lcd.init();
    lcd.setRotation(0); // retrato 240x320

    // Fondo rojo: si se ve, la inicialización y el SPI funcionan.
    lcd.fillScreen(lcd.color565(255, 0, 0));

    lcd.setTextColor(TFT_WHITE, TFT_RED);
    lcd.setTextSize(2);
    lcd.setCursor(20, 20);
    lcd.println("FinaGotchi");
    lcd.setCursor(20, 60);
    lcd.println("ILI9225 OK");
    lcd.setCursor(20, 100);
    lcd.println("240x320");

    Serial.println("FinaGotchi F1 (LovyanGFX): pintura completada");
}

void loop() { delay(2000); }
