# Assets de la GUI (Fase 24)

Aquí van las imágenes de la cerdita Nancy y los GIF de adorno. La app
**nunca se rompe si falta un archivo**: dibuja un placeholder rosa con el
nombre del estado. Nombres exactos esperados:

## Sprites (`sprites/`)

| Archivo | Cuándo se usa |
|---|---|
| `nancy_feliz.png` o `.gif` | Ánimo FELIZ en reposo (D03) |
| `nancy_preocupado.png` o `.gif` | Ánimo PREOCUPADO |
| `nancy_triste.png` o `.gif` | Ánimo TRISTE / D11 No entendí |
| `nancy_critico.png` o `.gif` | Ánimo CRITICO |
| `nancy_escuchando.png` o `.gif` | Grabando (D04) |
| `nancy_dormida.png` o `.gif` | Tras el cierre (D09) |
| `nancy_cierre.png` o `.gif` | Cierre del día (D09) |

Formato recomendado: PNG o GIF transparente, cuadrado (p. ej. 360×360).
Los GIF se animan solos (Pillow recorre los frames).

## GIF de adorno (`gifs/`)

| Archivo | Uso |
|---|---|
| `ola_grabando.gif` | D04 (opcional: se dibuja la onda) |
| `puntos_pensando.gif` | D05 Procesando (opcional) |

## Iconos (`iconos/`)

`wifi.png`, `battery.png`, `qr.png`, etc. Todos opcionales.

## Fuentes (`../fonts/`)

`Outfit.ttf` (headline) y `SpaceGrotesk.ttf` (body), licencia OFL.
Si no están, la GUI usa una fuente del sistema.
