"""Tema visual del simulador: paleta, fuentes y medidas.

Paleta del mockup del dispositivo:

- Primary ``#832D52``: pills oscuras y títulos.
- Secondary ``#F0AFC5``: tarjetas de Nancy y mensajes.
- Tertiary ``#B2CE45``: confirmaciones y éxito.
- Neutral ``#F6E5D1``: fondo base de la pantalla.

Tipografías: Outfit (headline) y Space Grotesk (body), en
``simulator/gui/fonts/``. Si los archivos no están, se usa una fuente
del sistema; la app nunca se rompe por falta de fuente.
"""

from pathlib import Path

FUENTES = Path(__file__).resolve().parent / "fonts"

PRIMARY = "#832D52"
SECONDARY = "#F0AFC5"
TERTIARY = "#B2CE45"
NEUTRAL = "#F6E5D1"
BORDE = "#0B5D3B"
TEXTO = "#2B1A22"

TAMANO_VENTANA = (480, 760)


def _registrar_fuentes_windows():
    """Registra los TTF locales en Windows para que Tk los vea por nombre."""
    try:
        import ctypes

        for archivo in FUENTES.glob("*.ttf"):
            ctypes.windll.gdi32.AddFontResourceW(str(archivo))
    except Exception:  # noqa: BLE001 - en otro SO o sin permiso, fallback
        pass


def registrar_fuentes():
    _registrar_fuentes_windows()
    return ("Outfit", "Space Grotesk")


def headline(tamano=22):
    return ("Outfit", tamano, "bold")


def cuerpo(tamano=14):
    return ("Space Grotesk", tamano)
