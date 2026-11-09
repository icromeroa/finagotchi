"""Instala el modelo de voz local de Nancy.

No versiona el modelo en el repositorio: lo descarga en
``%USERPROFILE%\\.finagotchi\\piper`` (o en ``FINAGOTCHI_VOICE_DIR`` si está
definida) y comprueba que se puede sintetizar una WAV.

    py -3 tools/configurar_voz.py
    py -3 tools/configurar_voz.py --voz es_MX-ald-x_low.onnx
"""

import argparse
import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
VOCES = {
    "es_MX-claude-high.onnx": "es/es_MX/claude/high/es_MX-claude-high.onnx",
    "es_MX-ald-x_low.onnx": "es/es_MX/ald/x_low/es_MX-ald-x_low.onnx",
}


def _contexto_ssl():
    """CA de certifi: el Python de macOS no siempre trae los certificados."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001 - sin certifi se usa el almacén del sistema
        return None


def _destino():
    ruta = Path(os.environ.get("FINAGOTCHI_VOICE_DIR") or Path.home() / ".finagotchi" / "piper")
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def _descargar(nombre, destino, ruta_hf):
    modelo = destino / nombre
    config = Path(str(modelo) + ".json")
    modelo_url = f"{BASE_URL}/{ruta_hf}"
    json_url = f"{BASE_URL}/{ruta_hf}.json"

    if modelo.exists() and config.exists():
        print(f"{nombre} ya está instalado.")
        return modelo

    print(f"Descargando {nombre} (puede tardar)...")
    with urllib.request.urlopen(
        modelo_url, timeout=600, context=_contexto_ssl()
    ) as respuesta, modelo.open("wb") as archivo:
        leidos = 0
        total = int(respuesta.headers.get("Content-Length") or 0)
        while True:
            bloque = respuesta.read(1024 * 1024)
            if not bloque:
                break
            archivo.write(bloque)
            leidos += len(bloque)
            if total:
                print(f"  {leidos * 100 // total} %", end="\r", flush=True)
    print("")

    print("Descargando configuración...")
    with urllib.request.urlopen(
        json_url, timeout=60, context=_contexto_ssl()
    ) as respuesta:
        config.write_bytes(respuesta.read())

    try:
        json.loads(config.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - la configuración dañada no es utilizable
        modelo.unlink(missing_ok=True)
        config.unlink(missing_ok=True)
        raise RuntimeError(f"La configuración de la voz está dañada: {exc}") from exc
    return modelo


def _verificar(nombre):
    destino = _destino()
    os.environ["PIPER_MODEL"] = str(destino / nombre)
    from backend import tts

    print("Verificando la voz...", end=" ")
    if not tts.disponible():
        print("FALLO")
        return 1
    audio = tts.sintetizar_wav("Nancy lista")
    if not audio or not audio.startswith(b"RIFF"):
        print("FALLO: no se produjo WAV")
        return 1
    print(f"OK ({len(audio)} bytes generados)")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--voz", choices=sorted(VOCES), default="es_MX-claude-high.onnx")
    parser.add_argument("--solo-verificar", action="store_true")
    args = parser.parse_args()

    destino = _destino()
    if not args.solo_verificar:
        modelo = _descargar(args.voz, destino, VOCES[args.voz])
        print(f"Voz instalada en: {modelo}")
    return _verificar(args.voz)


if __name__ == "__main__":
    raise SystemExit(main())
