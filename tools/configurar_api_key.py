"""Guarda la API key de Gemini FUERA del repositorio.

Uso:
    py -3 tools/configurar_api_key.py

La key se guarda en ``%USERPROFILE%/.finagotchi/gemini.env``. Ese archivo esta
fuera del proyecto, asi que ningun ``git clean``, borrado de carpeta o
reinstalacion lo puede borrar. El backend lo lee automaticamente.

Opciones:
    --mostrar      Muestra el estado actual sin cambiar nada.
    --tambien-local Copia la key tambien a ``backend/.env`` (ignorado por git).
    --modelo MODELO  Define el modelo principal.
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import ai  # noqa: E402

PREFIJO_TYPICO = "AIza"
PLANTILLA = """# Configuracion de FinaGotchi fuera del repositorio.
# Este archivo NUNCA se versiona: vive en tu carpeta de usuario.
# Se creo con tools/configurar_api_key.py

GEMINI_API_KEY={clave}
GEMINI_MODEL={modelo}
GEMINI_MODEL_FALLBACKS={respaldos}
"""


def parse_args():
    parser = argparse.ArgumentParser(description="Configurar la API key de Gemini")
    parser.add_argument("--mostrar", action="store_true", help="Solo mostrar el estado")
    parser.add_argument(
        "--tambien-local",
        action="store_true",
        help="Copiar la key tambien a backend/.env (ignorado por git)",
    )
    parser.add_argument("--modelo", default=None, help="Modelo principal de transcripcion")
    return parser.parse_args()


def mostrar_estado():
    origen = ai.origen_de_la_key()
    print("Estado de la configuracion de Gemini")
    print(f"  Archivo externo : {ai.ARCHIVO_EXTERNO}")
    print(f"  Existe          : {'si' if ai.ARCHIVO_EXTERNO.exists() else 'no'}")
    print(f"  Key encontrada  : {'si' if ai.esta_configurado() else 'NO'}")
    print(f"  Origen          : {origen or 'ninguno'}")
    print(f"  Modelo          : {ai.modelo()}")
    print(f"  Cadena de modelos: {', '.join(ai.cadena_modelos())}")
    return 0 if ai.esta_configurado() else 1


def guardar(clave, modelo, respaldos, destino: Path):
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        PLANTILLA.format(clave=clave, modelo=modelo, respaldos=respaldos),
        encoding="utf-8",
    )
    try:
        os.chmod(destino, 0o600)
    except OSError:
        pass


def main():
    args = parse_args()
    if args.mostrar:
        return mostrar_estado()

    print("API key de Gemini (https://aistudio.google.com -> Get API key)")
    print("La clave no se muestra mientras la escribes ni queda en el repositorio.")
    clave = getpass.getpass("Pega la API key: ").strip()
    if not clave:
        print("No se ingreso ninguna clave.")
        return 1
    if not clave.startswith(PREFIJO_TYPICO):
        print(
            f"Aviso: las claves de Google suelen empezar con '{PREFIJO_TYPICO}'. "
            "Se guardara igual, pero revisa que la copiaste completa."
        )

    modelo = args.modelo or "gemini-3.5-flash"
    respaldos = "gemini-3.5-flash-lite,gemini-3.8-flash"

    guardar(clave, modelo, respaldos, ai.ARCHIVO_EXTERNO)
    print(f"\nGuardada en {ai.ARCHIVO_EXTERNO}")

    if args.tambien_local:
        guardar(clave, modelo, respaldos, ROOT / "backend" / ".env")
        print(f"Copiada tambien a {ROOT / 'backend' / '.env'} (ignorado por git)")

    # Se comprueba contra la API real para no dejar una key que no funcione.
    os.environ["GEMINI_API_KEY"] = clave
    os.environ["GEMINI_MODEL"] = modelo
    os.environ["GEMINI_MODEL_FALLBACKS"] = respaldos
    try:
        from google import genai

        cliente = genai.Client(api_key=clave)
        modelos = [m.name for m in cliente.models.list()]
        print(f"Key valida. Modelos disponibles en la cuenta: {len(modelos)}")
        if modelo not in modelos and f"models/{modelo}" not in modelos:
            print(
                f"Aviso: '{modelo}' no aparece en la lista de la cuenta. "
                f"Disponibles con 'flash': "
                f"{', '.join(n for n in modelos if 'flash' in n)[:200]}"
            )
    except Exception as exc:  # noqa: BLE001
        print(f"No se pudo verificar la key contra la API: {type(exc).__name__}: {exc}")
        print("Revisa que la clave sea correcta y que la cuota este activa.")
        return 1

    print("\nListo. Reinicia el backend para que tome la configuracion:")
    print("    py -3 backend/server.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
