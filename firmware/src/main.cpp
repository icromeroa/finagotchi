/**
 * FinaGotchi — Firmware F1 (prueba mínima de pantalla ILI9225)
 *
 * Objetivo: salir de la pantalla blanca. Solo inicializa la pantalla
 * ILI9225 (240x320) con TFT_eSPI y pinta un rectángulo rojo con texto
 * "FinaGotchi". Sin micrófono, sin red, sin botones.
 *
 * Conexión verificada (ver docs/FIRMWARE.md):
 *   VCC  -> 3V3
 *   GND  -> GND
 *   SCL  -> GP12 (SCLK)
 *   SDA  -> GP11 (MOSI)
 *   RES  -> GP9  (RST)
 *   DC   -> GP10 (DC)
 *   CS   -> GP13 (CS) — primero como GPIO; si se atora, bajar a GND
 */

#include <Arduino.h>
#include <TFT_eSPI.h>

// TFT_eSPI está configurada por -D en platformio.ini (ILI9225_DRIVER,
// 240x320, MOSI=11, SCLK=12, CS=13, DC=10, RST=9).
TFT_eSPI tft = TFT_eSPI();

void setup() {
    Serial.begin(115200);
    delay(100);
    Serial.println("FinaGotchi F1: iniciando pantalla ILI9225 240x320");
    Serial.println("MOSI=GP11 SCLK=GP12 CS=GP13 DC=GP10 RST=GP9");

    tft.init();
    tft.setRotation(0); // retrato 240x320

    // Fondo rojo: si se ve, la inicialización y el SPI funcionan.
    tft.fillScreen(TFT_RED);

    tft.setTextColor(TFT_WHITE, TFT_RED);
    tft.setTextSize(2);
    tft.setCursor(20, 20);
    tft.println("FinaGotchi");
    tft.setCursor(20, 60);
    tft.println("ILI9225 OK");
    tft.setCursor(20, 100);
    tft.println("240x320");

    Serial.println("FinaGotchi F1: pintura completada");
}

void loop() {
    delay(2000);
}
