"""Graba los clips del dataset de evaluacion.

Uso:
    py -3 tools/grabar_dataset.py

Recorre el manifiesto, muestra la frase que hay que decir y graba el WAV
mientras se mantenga presionada la tecla ESPACIO. Al terminar actualiza la
columna ``duracion_s`` del manifiesto.

Los audios quedan en ``datasets/eval_audio/audio`` y no se versionan.
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATASET = ROOT / "datasets" / "eval_audio"
MANIFEST = DATASET / "manifest.csv"
AUDIO_DIR = DATASET / "audio"
SAMPLE_RATE = 16000
MAX_SEGUNDOS = 40


def parse_args():
    parser = argparse.ArgumentParser(description="Grabar el dataset de audio")
    parser.add_argument("--solo", nargs="*", help="IDs a grabar (por defecto todos)")
    parser.add_argument(
        "--sin-tecla",
        action="store_true",
        help="Graba un clip por enter en vez de por la tecla ESPACIO",
    )
    return parser.parse_args()


def cargar_manifest():
    with MANIFEST.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def guardar_manifest(filas):
    campos = list(filas[0].keys())
    with MANIFEST.open("w", encoding="utf-8", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)


def grabar(ruta):
    try:
        import keyboard
    except ImportError:
        keyboard = None

    print("  Mantén presionada la tecla ESPACIO mientras hablas. Suelta para terminar.")
    while not keyboard.is_pressed("space"):
        time.sleep(0.05)

    bloques = []
    inicio = time.time()

    def callback(indata, frames, time_info, status):
        bloques.append(indata.copy())

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=callback
    ):
        while keyboard.is_pressed("space"):
            time.sleep(0.05)

    duracion = round(time.time() - inicio, 1)
    if not bloques:
        return 0.0
    muestras = np.concatenate(bloques, axis=0)
    if duracion > MAX_SEGUNDOS:
        muestras = muestras[: SAMPLE_RATE * MAX_SEGUNDOS]
        duracion = MAX_SEGUNDOS
    wav.write(ruta, SAMPLE_RATE, muestras)
    return duracion


def main():
    args = parse_args()
    try:
        import keyboard
    except ImportError:
        print("Falta la libreria keyboard: py -3 -m pip install keyboard")
        return 1

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    filas = cargar_manifest()
    pendientes = [f for f in filas if not (DATASET / f["archivo"]).exists()]
    if args.solo:
        pendientes = [f for f in pendientes if f["id"] in set(args.solo)]

    if not pendientes:
        print("No hay clips pendientes de grabacion.")
        return 0

    print(f"Clips pendientes: {len(pendientes)}\n")
    for fila in pendientes:
        print(f"[{fila['id']}] Di: \"{fila['transcripcion']}\"")
        duracion = grabar(DATASET / fila["archivo"])
        fila["duracion_s"] = f"{duracion:.1f}"
        print(f"  Guardado {fila['archivo']} ({duracion:.1f}s)\n")

    guardar_manifest(filas)
    print("Manifiesto actualizado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
