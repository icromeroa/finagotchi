"""Genera el banco de frases cortas del simulador con Piper.

Uso:

    py -3 tools/generar_voz.py

El audio se guarda en ``simulator/assets/voz`` y puede versionarse en git.
Las frases son cortas y predictibles; las oraciones dinamicas no se
pregraban: se sintetizan en tiempo real con ``backend/tts.py``.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import tts  # noqa: E402

VOZ = ROOT / "simulator" / "assets" / "voz"

FRASES = {
    "confirmar.wav": "¿Está correcto?",
    "resultado.wav": "Listo",
    "cancelado.wav": "Cancelado",
    "entendido.wav": "Entendido",
    "no_entendio.wav": "No entendí",
    "sin_conexion.wav": "Sin conexión",
    "microfono_bajo.wav": "Revisa el micrófono",
}


def main():
    if not tts.disponible():
        print("Piper o su modelo no están disponibles.")
        return 1
    VOZ.mkdir(parents=True, exist_ok=True)
    for nombre, texto in FRASES.items():
        audio = tts.sintetizar_wav(texto)
        if audio is None:
            print(f"No se pudo sintetizar {nombre}.")
            return 1
        (VOZ / nombre).write_bytes(audio)
        print(f"Generada {nombre} ({len(audio)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
