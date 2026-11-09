"""Sintetizador local de voz para Nancy.

El backend genera WAV en memoria, nunca escribe el audio en disco ni en la
base de datos. Usa `piper-tts` con un modelo local espanol. Si el modelo no
está disponible, la aplicación sigue funcionando: el cliente solo muestra
texto y el servidor responde sin ``voz``.
"""

import os
import threading
import wave
from pathlib import Path

MODEL_DIR = Path.home() / ".finagotchi" / "piper"
MAX_CARACTERES = 400
TIMEOUT_S = float(os.environ.get("TTS_TIMEOUT_S") or 20)

_SINGLE = None
_LOCK = threading.RLock()


def model_path():
    """Devuelve el modelo configurado o el instalado por defecto."""
    configurado = (os.environ.get("PIPER_MODEL") or "").strip()
    if configurado:
        ruta = Path(configurado).expanduser()
        return ruta if ruta.is_file() else None
    candidatos = sorted(MODEL_DIR.glob("*.onnx"))
    return candidatos[0] if candidatos else None


def config_path(ruta_modelo):
    configurado = (os.environ.get("PIPER_CONFIG") or "").strip()
    if configurado:
        ruta = Path(configurado).expanduser()
        return ruta if ruta.is_file() else None
    ruta_json = Path(str(ruta_modelo) + ".json")
    return ruta_json if ruta_json.is_file() else None


def disponible():
    """True si Piper y el modelo local estan instalados."""
    modelo = model_path()
    if modelo is None:
        return False
    if config_path(modelo) is None:
        return False
    try:
        from piper.voice import PiperVoice  # noqa: F401
    except Exception:  # noqa: BLE001 - falta la libreria
        return False
    return True


def _voz():
    global _SINGLE
    with _LOCK:
        if _SINGLE is None:
            from piper.voice import PiperVoice

            modelo = model_path()
            _SINGLE = PiperVoice.load(modelo, config_path(modelo))
        return _SINGLE


def sintetizar_wav(texto):
    """Devuelve bytes WAV de ``texto`` o None si TTS no esta disponible."""
    texto = " ".join(str(texto or "").split()).strip()
    if not texto or len(texto) > MAX_CARACTERES:
        return None
    modelo = model_path()
    if not disponible():
        return None

    import io

    buffer = io.BytesIO()
    try:
        with wave.open(buffer, "wb") as wav_file:
            with _LOCK:
                _voz().synthesize_wav(texto, wav_file)
    except Exception:  # noqa: BLE001 - una falla no debe tumbar la petición
        return None
    return buffer.getvalue()


def informacion():
    return {
        "modelo": str(model_path() or ""),
        "max_caracteres": MAX_CARACTERES,
        "latencia_max_s": TIMEOUT_S,
    }
