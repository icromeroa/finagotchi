"""Sprites de Nancy (PNG o GIF) con respaldo dibujado.

Los archivos van en ``simulator/gui/assets/sprites/`` (cerditas) y
``simulator/gui/assets/gifs/`` (animaciones sueltas). Nombres esperados:
``nancy_<estado>.png`` o ``.gif``; también se acepta el alias femenino
``nancy_preocupada`` para el estado ``preocupado``. Si un estado no tiene
archivo, se genera un placeholder rosa con el nombre del estado: la GUI
nunca se rompe por falta de arte.

Los GIF se descomponen en frames con Pillow; el widget que los muestra
recorre los frames con ``after()``. El arte conserva su proporción
vertical (no se estira a cuadrado).
"""

from pathlib import Path

import customtkinter as ctk
from PIL import Image

RAIZ = Path(__file__).resolve().parent
SPRITES = RAIZ / "assets" / "sprites"
GIFS = RAIZ / "assets" / "gifs"
ANCHO_SPRITE = 180

ESTADOS = (
    "feliz",
    "preocupado",
    "triste",
    "critico",
    "escuchando",
    "dormida",
    "cierre",
    "ola",
    "puntos",
)

_ALIASES = {
    "preocupado": ("preocupado", "preocupada"),
    "ola": ("ola", "ola_grabando"),
    "puntos": ("puntos", "puntos_pensando"),
}


def _candidatos(estado):
    estado = str(estado or "feliz").lower()
    nombres = _ALIASES.get(estado, (estado,))
    rutas = []
    for nombre in nombres:
        for carpeta in (SPRITES, GIFS):
            for extension in (".gif", ".png"):
                rutas.append(carpeta / f"nancy_{nombre}{extension}")
                rutas.append(carpeta / f"{nombre}{extension}")
    return rutas


def _ajustar(imagen, tamano):
    copia = imagen.convert("RGBA").copy()
    copia.thumbnail((tamano, tamano), Image.LANCZOS)
    lienzo = Image.new("RGBA", (tamano, tamano), "#F0AFC5")
    lienzo.alpha_composite(copia, ((tamano - copia.width) // 2, (tamano - copia.height) // 2))
    return lienzo.convert("RGB")


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
    ruta = next((r for r in _candidatos(estado) if r.exists()), None)
    frames = []
    duracion = 100
    try:
        if ruta is not None and ruta.suffix.lower() == ".gif":
            with Image.open(ruta) as con_gif:
                while True:
                    frame = _ajustar(con_gif.convert("RGB"), tamano)
                    frames.append(frame)
                    try:
                        duracion = int(con_gif.info.get("duration") or 100)
                    except Exception:  # noqa: BLE001
                        pass
                    try:
                        con_gif.seek(con_gif.tell() + 1)
                    except EOFError:
                        break
        elif ruta is not None:
            with Image.open(ruta) as png:
                frames = [_ajustar(png.convert("RGB"), tamano)]
    except Exception:  # noqa: BLE001 - sin sprite válido, placeholder
        frames = []
    if not frames:
        frames = [_placeholder(estado, tamano)]
    return frames, duracion


def foto(frame, tamano=ANCHO_SPRITE):
    """Convierte un frame PIL a foto Tk (hay que conservar la referencia)."""
    return ctk.CTkImage(light_image=frame, size=(tamano, tamano))
