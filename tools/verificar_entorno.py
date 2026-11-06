"""Diagnostico del entorno de FinaGotchi.

Uso:
    py -3 tools/verificar_entorno.py

Revisa, en este orden:
- Version de Python y dependencias instaladas.
- Estado del esquema de la base de datos.
- De donde viene la API key de Gemini y si la API responde.
- Si el microfono esta disponible para el simulador.

Devuelve 0 si todo esta bien y 1 si hay algo que arreglar.
"""

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import ai  # noqa: E402


def ok(texto):
    print(f"  [ok]   {texto}")


def aviso(texto):
    print(f"  [aviso] {texto}")


def error(texto):
    print(f"  [error] {texto}")


def revisar_python():
    print("Python y dependencias")
    version = ".".join(str(n) for n in sys.version_info[:3])
    ok(f"Python {version}")
    faltantes = []
    for paquete, etiqueta in (
        ("flask", "Flask"),
        ("google.genai", "google-genai"),
        ("dotenv", "python-dotenv"),
        ("requests", "requests"),
        ("sounddevice", "sounddevice"),
        ("scipy", "scipy"),
        ("numpy", "numpy"),
        ("keyboard", "keyboard"),
    ):
        try:
            importlib.import_module(paquete)
            ok(etiqueta)
        except ImportError:
            faltantes.append(etiqueta)
            error(f"{etiqueta} no esta instalado")
    if faltantes:
        aviso("Instala lo que falta con: py -3 -m pip install -r requirements.txt")
    return not faltantes


def revisar_base():
    print("Base de datos")
    ruta = ROOT / "finagotchi.db"
    if not ruta.exists():
        error(f"No existe {ruta.name}. Creala con: py -3 database/init_db.py")
        return False
    try:
        import sqlite3

        conn = sqlite3.connect(str(ruta))
        version = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        fallos = conn.execute("PRAGMA foreign_key_check").fetchall()
        conn.close()
    except Exception as exc:  # noqa: BLE001
        error(f"No se pudo abrir la base: {exc}")
        return False
    ok(f"Esquema v{version}")
    if fallos:
        error(f"foreign_key_check devolvio {len(fallos)} problemas")
        return False
    ok("foreign_key_check sin errores")
    return True


def revisar_ia():
    print("Proveedor de transcripcion")
    print(f"  Modo configurado: {ai.proveedor_preferido()}")

    local_ok = ai.local_disponible()
    if local_ok:
        ok(f"Proveedor local disponible (faster-whisper, modelo {ai.modelo_local()})")
    else:
        aviso(
            "Proveedor local no disponible: falta faster-whisper "
            "(py -3 -m pip install faster-whisper)"
        )

    origen = ai.origen_de_la_key()
    if not ai.esta_configurado():
        error("No hay API key de Gemini")
        aviso(
            "Genera una key en https://aistudio.google.com y ejecuta: "
            "py -3 tools/configurar_api_key.py"
        )
        if local_ok:
            aviso("Igual se puede transcribir con el modelo local.")
            return True
        return False

    ok(f"Key cargada desde: {origen}")
    ok(f"Modelo principal: {ai.modelo()}")
    ok(f"Cadena de modelos: {', '.join(ai.cadena_modelos())}")

    try:
        from google import genai

        cliente = genai.Client(api_key=ai.api_key())
        modelos = [m.name.replace("models/", "") for m in cliente.models.list()]
        ok(f"La API responde. {len(modelos)} modelos disponibles")
        for candidato in ai.cadena_modelos():
            marca = "ok" if candidato in modelos else "no disponible"
            aviso(f"  {candidato}: {marca}")
        return True
    except Exception as exc:  # noqa: BLE001
        codigo = getattr(exc, "code", None)
        if codigo == 401:
            error("Google rechazo la API key (401)")
            prefijo = ai.api_key()[:4]
            if prefijo.startswith("AQ"):
                aviso(
                    "Es una 'Auth key' (AQ.Ab). Desde el 28 de mayo de 2026 AI Studio "
                    "solo emite claves AQ y hay un problema abierto de compatibilidad: "
                    "devuelven 401 ACCESS_TOKEN_TYPE_UNSUPPORTED."
                )
            aviso(
                "Opciones: usar una clave Standard (AIza) de otro proyecto, "
                "pedir revision de la cuenta a Google, o dejar STT_PROVEEDOR=local."
            )
        elif codigo == 403:
            error("La clave no tiene permiso (403). Revisa la Generative Language API.")
        elif codigo == 429:
            aviso("Cuota agotada (429). Es temporal.")
        else:
            error(f"La API no responde: {type(exc).__name__}: {str(exc)[:200]}")
        if local_ok:
            aviso("El modelo local puede transcribir igual: no hay bloqueo.")
            return True
        return False


def revisar_llm():
    print("Modelo de IA para interpretar la frase")
    print(f"  Proveedor configurado: {ai.proveedor_llm() or 'ninguno'}")
    if ai.ollama_disponible():
        ok(f"Ollama disponible con el modelo '{ai.modelo_ollama()}'")
        ok(f"URL: {ai.url_ollama()}")
        return True
    aviso(
        "Ollama no esta disponible (no responde o falta el modelo "
        f"'{ai.modelo_ollama()}')."
    )
    aviso(
        "Instalalo con: winget install --id Ollama.Ollama --exact --silent  "
        "y despues: ollama pull " + ai.modelo_ollama()
    )
    if ai.esta_configurado():
        aviso("Se puede usar Gemini para la interpretacion si la clave funciona.")
    else:
        aviso("Sin LLM el backend usa las reglas por palabra clave.")
    return False


def revisar_microfono():
    print("Microfono para el simulador")
    try:
        import sounddevice as sd
    except ImportError:
        aviso("sounddevice no esta instalado: el simulador no podra grabar")
        return False
    try:
        dispositivo = sd.query_devices(kind="input")
        ok(f"Entrada por defecto: {dispositivo['name']}")
        ok(
            "El simulador graba a 16 kHz mono; el puerto resamplea solo"
        )
    except Exception as exc:  # noqa: BLE001
        error(f"No hay microfono disponible: {exc}")
        return False
    return True


def main():
    print("=== Verificacion del entorno de FinaGotchi ===\n")
    resultados = [
        revisar_python(),
        revisar_base(),
        revisar_ia(),
        revisar_llm(),
        revisar_microfono(),
    ]
    print()
    if all(resultados):
        print("Todo listo. Puedes levantar el backend con: py -3 backend/server.py")
        return 0
    print("Hay pendientes. Revisa los mensajes de arriba.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
