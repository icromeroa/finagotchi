"""Sprites de Nancy (PNG o GIF) con respaldo dibujado.

Los archivos van en ``simulator/gui/assets/sprites/`` con el nombre
``nancy_<estado>.png`` o ``.gif`` (ver ``assets/README.md``). Si un estado
no tiene archivo, se genera un placeholder rosa con el nombre del estado:
la GUI nunca se rompe por falta de arte.

Los GIF se descomponen en frames con Pillow; el widget que los muestra
recorre los frames con ``after()``.
"""

from pathlib import Path

import customtkinter as ctk
from PIL import Image

ASSETS = Path(__file__).resolve().parent / "assets" / "sprites"
ANCHO_SPRITE = 180

ESTADOS = (
    "feliz",
    "preocupado",
    "triste",
    "critico",
    "escuchando",
    "dormida",
    "cierre",
)


def _ruta(estado, extension):
    return ASSETS / f"nancy_{estado}{extension}"


def _placeholder(estado, tamano=ANCHO_SPRITE):
    from PIL import ImageDraw

    imagen = Image.new("RGB", (tamano, tamano), (240, 175, 197))
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rectangle((20, 20, tamano - 20, tamano - 20), outline=(131, 45, 82), width=6)
    try:
        dibujo.text((tamano // 2 - 40, tamano // 2 - 8), estado, fill=(43, 26, 34))
    except Exception:  # noqa: BLE001 - el texto del placeholder es opcional
        pass
    return imagen


def cargar_frames(estado, tamano=ANCHO_SPRITE):
    """Devuelve ``(frames, duracion_ms)`` para un estado; nunca lanza."""
    estado = str(estado or "feliz").lower()
    gif = _ruta(estado, ".gif")
    png = _ruta(estado, ".png")
    frames = []
    duracion = 100
    try:
        if gif.exists():
            with Image.open(gif) as con_gif:
                while True:
                    frame = con_gif.convert("RGB").resize((tamano, tamano))
                    frames.append(frame)
                    try:
                        duracion = int(con_gif.info.get("duration") or 100)
                    except Exception:  # noqa: BLE001
                        pass
                    try:
                        con_gif.seek(con_gif.tell() + 1)
                    except EOFError:
                        break
        elif png.exists():
            frames = [Image.open(png).convert("RGB").resize((tamano, tamano))]
    except Exception:  # noqa: BLE001 - sin sprite válido, placeholder
        frames = []
    if not frames:
        frames = [_placeholder(estado, tamano)]
    return frames, duracion


def foto(frame, tamano=ANCHO_SPRITE):
    """Convierte un frame PIL a foto Tk (hay que conservar la referencia)."""
    return ctk.CTkImage(light_image=frame, size=(tamano, tamano))
