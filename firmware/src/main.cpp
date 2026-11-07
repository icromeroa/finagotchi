/**
 * FinaGotchi — Firmware F1 (prueba mínima de pantalla ILI9225 con U8g2)
 *
 * Objetivo: salir de la pantalla blanca. Solo inicializa la pantalla
 * ILI9225 (240x320) con U8g2 y pinta fondo + texto "FinaGotchi".
 * Sin micrófono, sin red, sin botones.
 *
 * Conexión final (ver docs/FIRMWARE.md):
 *   VCC  -> 3V3
 *   GND  -> GND
 *   SCL (SCK) Pin 2  -> GP2
 *   SDA (MOSI) Pin 13 -> GP13
 *   RES (RST) Pin 5  -> GP5
 *   DC Pin 6         -> GP6
 *   CS Pin 7         -> GP7  (Mover desde GND! U8g2 maneja CS por software.
 *                             Dejarlo en GND causaría cortocircuito cuando
 *                             el driver lo pone en alto.)
 */

#include <Arduino.h>
#include <SPI.h>
#include <U8g2lib.h>

// Pines ILI9225 (tu cableado real)
static const int8_t PIN_SCL = 2;   // GP2
static const int8_t PIN_SDA = 13;  // GP13
static const int8_t PIN_DC  = 6;   // GP6
static const int8_t PIN_RST = 5;   // GP5
static const int8_t PIN_CS  = 7;   // GP7

// U8G2 ILI9225 240x320, SPI por hardware, fuente "F" = full buffer
U8G2_ILI9225_240X320_F_HW_SPI u8g2(U8G2_R0, PIN_DC, PIN_CS, PIN_RST);

void setup() {
    Serial.begin(115200);
    delay(100);
    Serial.println("FinaGotchi F1 (U8g2): iniciando pantalla ILI9225 240x320");
    Serial.println("MOSI=GP13 SCLK=GP2 CS=GP7 DC=GP6 RST=GP5");

    // SPI en pines propios (SuperMini: GP2/GP13, no los por defecto)
    SPI.begin(PIN_SCL, -1, PIN_SDA, PIN_CS);

    u8g2.begin();
    u8g2.setBusClock(10000000);  // 10 MHz a prueba: si no pinta, bajar a 5 MHz

    u8g2.firstPage();
    do {
        u8g2.drawBox(0, 0, 240, 320);  // fondo relleno
        u8g2.setFont(u8g2_font_ncenB14_tr);
        u8g2.setDrawColor(0);          // negro sobre fondo (drawBox rellena con color 1)
        u8g2.drawStr(45, 150, "FinaGotchi");
        u8g2.drawStr(60, 170, "ILI9225 OK");
        u8g2.drawStr(75, 190, "240x320");
    } while (u8g2.nextPage());

    Serial.println("FinaGotchi F1 (U8g2): pintura completada");
}

void loop() {
    delay(2000);
}
