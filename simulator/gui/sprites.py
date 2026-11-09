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


def _recortar_diptych(imagen):
    """Si el frame es un díptico vertical (escena oscura sobre clara), deja la clara.

    Los GIF de Nancy traen dos escenas apiladas (arriba silueta blanca sobre
    negro, abajo la cerdita en color). Se detecta el salto de luminancia en
    el tercio medio y se conserva solo la mitad clara.
    """
    try:
        import numpy as np

        arreglo = np.array(imagen.convert("RGB")).astype(int)
        alto = arreglo.shape[0]
        if alto < 100:
            return imagen
        luminancia = arreglo.mean(axis=(1, 2))
        inicio, fin = int(alto * 0.35), int(alto * 0.65)
        if fin <= inicio:
            return imagen
        diferencias = np.abs(np.diff(luminancia[inicio:fin]))
        if len(diferencias) == 0:
            return imagen
        corte = inicio + int(diferencias.argmax())
        if diferencias.max() < 80:
            return imagen
        arriba = luminancia[: corte + 1].mean()
        abajo = luminancia[corte + 1 :].mean()
        if arriba < 100 and abajo >= 100:
            return imagen.crop((0, corte + 1, imagen.width, alto))
        if abajo < 100 and arriba >= 100:
            return imagen.crop((0, 0, imagen.width, corte + 1))
    except Exception:  # noqa: BLE001 - ante la duda, frame completo
        pass
    return imagen


def _sin_fondo(imagen, tolerancia=36):
    """Hace transparente el fondo conectado al borde (negro o blanco).

    Inundación desde los bordes: solo el fondo que toca el borde se vuelve
    transparente; los blancos interiores (ojos, brillos) se conservan.
    """
    from collections import deque

    rgba = imagen.convert("RGBA")
    try:
        import numpy as np

        arreglo = np.array(rgba).astype(int)
        alto, ancho = arreglo.shape[:2]
        esquina = arreglo[0, 0, :3]
        fondo = (
            (np.abs(arreglo[..., 0] - esquina[0]) <= tolerancia)
            & (np.abs(arreglo[..., 1] - esquina[1]) <= tolerancia)
            & (np.abs(arreglo[..., 2] - esquina[2]) <= tolerancia)
        )
        visitado = np.zeros(fondo.shape, dtype=bool)
        cola = deque()
        for x in range(ancho):
            for y in (0, alto - 1):
                if fondo[y, x] and not visitado[y, x]:
                    visitado[y, x] = True
                    cola.append((x, y))
        for y in range(alto):
            for x in (0, ancho - 1):
                if fondo[y, x] and not visitado[y, x]:
                    visitado[y, x] = True
                    cola.append((x, y))
        while cola:
            x, y = cola.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < ancho and 0 <= ny < alto and fondo[ny, nx] and not visitado[ny, nx]:
                    visitado[ny, nx] = True
                    cola.append((nx, ny))
        arreglo[..., 3] = np.where(visitado, 0, arreglo[..., 3])
        rgba = Image.fromarray(arreglo.astype("uint8"), "RGBA")
    except Exception:  # noqa: BLE001 - sin numpy, conserva el arte
        pass
    caja = rgba.getbbox()
    return rgba.crop(caja) if caja else rgba


def _sin_negro(imagen):
    """Compatibilidad: fondo transparente y recorte (ver ``_sin_fondo``)."""
    return _sin_fondo(_recortar_diptych(imagen))


def _ajustar(imagen, tamano):
    copia = _sin_negro(imagen)
    copia.thumbnail((tamano, tamano), Image.NEAREST)
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
