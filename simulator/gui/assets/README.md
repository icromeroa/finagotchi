# Assets de la GUI (Fase 24)

Aquí van las imágenes de la cerdita Nancy y los GIF de adorno. La app
**nunca se rompe si falta un archivo**: dibuja un placeholder rosa con el
nombre del estado. Nombres exactos esperados:

## Sprites (`sprites/`)

| Archivo | Cuándo se usa |
|---|---|
| `nancy_feliz.png` o `.gif` | Ánimo FELIZ en reposo (D03) |
| `nancy_preocupada.png` o `.gif` | Ánimo PREOCUPADO (también vale `nancy_preocupado`) |
| `nancy_triste.png` o `.gif` | Ánimo TRISTE / D11 No entendí |
| `nancy_critico.png` o `.gif` | Ánimo CRITICO |
| `nancy_dormida.png` o `.gif` | Tras el cierre (D09) |

Formato recomendado: PNG o GIF transparente, cuadrado o vertical. Los GIF
se animan solos (Pillow recorre los frames) y conservan su proporción.

## Animaciones (`gifs/`)

| Archivo | Cuándo se usa |
|---|---|
| `nancy_escuchando.gif` | Nancy escuchando (reposo conversacional) |
| `nancy_cierre.gif` | Cierre del día |
| `ola_grabando.gif` | Onda mientras se graba (D04) |
| `puntos_pensando.gif` | Puntos mientras se procesa (D05) |

Los originales en MP4 se conservan como `*.mp4` de referencia; la GUI
carga los GIF ya.convertidos. Si falta un GIF, se usa el placeholder.

## Iconos (`iconos/`)

`wifi.png`, `battery.png`, `qr.png`, etc. Todos opcionales.

## Fuentes (`../fonts/`)

`Outfit.ttf` (headline) y `SpaceGrotesk.ttf` (body), licencia OFL.
Si no están, la GUI usa una fuente del sistema.
