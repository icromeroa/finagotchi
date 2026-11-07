"""Cliente de prueba para el puente Xiaozhi-FinaGotchi.

Sirve para validar el puente sin placas ni servidor Xiaozhi:

    py -3 cliente_prueba.py "gasté 20 mil en almuerzo"
    py -3 cliente_prueba.py "sí"
    py -3 cliente_prueba.py "¿cuánto gasté ayer?" --voz

La opción ``--voz`` reproduce el WAV en memoria (Windows). No guarda audio.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib import error, request

try:
    import winsound
except ImportError:  # pragma: no cover - solo Windows
    winsound = None

DEFAULT_BRIDGE_URL = os.environ.get("XIAOZHI_BRIDGE_URL", "http://127.0.0.1:8787")


def _peticion(url, payload, timeout=90):
    cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    peticion = request.Request(
        url,
        data=cuerpo,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(peticion, timeout=timeout) as respuesta:
            return respuesta.status, respuesta.headers.get("Content-Type", ""), respuesta.read()
    except error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()
    except error.URLError as exc:
        raise SystemExit(
            f"No pude conectar con el puente en {url}: {exc.reason}\n"
            "¿Está corriendo 'py -3 bridge.py'?"
        ) from exc


def enviar_turno(bridge_url, texto):
    estado, _tipo, cuerpo = _peticion(f"{bridge_url.rstrip('/')}/turno", {"texto": texto})
    datos = json.loads(cuerpo.decode("utf-8"))
    return estado, datos


def pedir_audio(bridge_url, texto):
    estado, tipo, cuerpo = _peticion(
        f"{bridge_url.rstrip('/')}/sintetizar", {"texto": texto}
    )
    if estado != 200 or "audio" not in (tipo or "").lower():
        return None
    return cuerpo


def reproducir(audio):
    if not audio:
        return False
    if winsound is None:
        print("(Este sistema no tiene winsound; omite --voz o reproduce el WAV tú mismo.)")
        return False
    winsound.PlaySound(audio, winsound.SND_MEMORY)
    return True


def imprimir(respuesta):
    if not respuesta.get("ok", False):
        print("ERROR:", json.dumps(respuesta.get("error"), ensure_ascii=False))
        return
    print(f"NANCY (voz):    {respuesta.get('hablar') or '(sin texto)'}")
    print(f"NANCY (pantalla): {respuesta.get('mensaje_nancy') or '(sin texto)'}")
    print(f"tipo: {respuesta.get('tipo_respuesta')} | confirmar: {respuesta.get('requiere_confirmacion')}")
    datos = respuesta.get("datos") or {}
    if datos:
        print("datos:", json.dumps(datos, ensure_ascii=False)[:800])


def un_turno(bridge_url, texto, voz):
    estado, respuesta = enviar_turno(bridge_url, texto)
    if estado >= 500 and not respuesta.get("hablar"):
        print(f"HTTP {estado}")
    imprimir(respuesta)
    if voz and respuesta.get("ok"):
        audio = pedir_audio(bridge_url, respuesta.get("hablar") or "")
        reproducir(audio)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Prueba el puente Xiaozhi-FinaGotchi sin placas."
    )
    parser.add_argument("texto", nargs="?", help="Frase a enviar; si se omite, modo interactivo.")
    parser.add_argument("--bridge-url", default=DEFAULT_BRIDGE_URL)
    parser.add_argument(
        "--voz", action="store_true", help="Reproduce el WAV de la respuesta (Windows)."
    )
    args = parser.parse_args(argv)

    if args.texto:
        un_turno(args.bridge_url, args.texto, args.voz)
        return 0

    print("Modo interactivo. Escribe 'salir' para terminar.")
    while True:
        try:
            texto = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not texto:
            continue
        if texto.lower() in ("salir", "exit", "quit"):
            break
        un_turno(args.bridge_url, texto, args.voz)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
