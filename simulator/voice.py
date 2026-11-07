"""Reproducción de voz en el simulador.

La voz online usa `POST /device/voice/synthesize`; la voz offline usa el banco
de frases pregrabadas en ``simulator/assets/voz``. Si no hay dispositivo de
audio o el backend no tiene Piper, el simulador sigue mostrando el texto.
"""

from pathlib import Path

try:
    import winsound
except Exception:  # noqa: BLE001 - requiere Windows o una API de audio
    winsound = None

RAIZ = Path(__file__).resolve().parent.parent

FRASES = {
    "confirmacion": RAIZ / "simulator" / "assets" / "voz" / "confirmar.wav",
    "resultado": RAIZ / "simulator" / "assets" / "voz" / "resultado.wav",
    "cancelado": RAIZ / "simulator" / "assets" / "voz" / "cancelado.wav",
    "aclaracion": RAIZ / "simulator" / "assets" / "voz" / "no_entendio.wav",
    "error": RAIZ / "simulator" / "assets" / "voz" / "microfono_bajo.wav",
}

_ACTIVADO = False


def iniciar(activado=True):
    global _ACTIVADO
    _ACTIVADO = bool(activado)
    return _ACTIVADO


def activo():
    return _ACTIVADO


def alternar():
    global _ACTIVADO
    _ACTIVADO = not _ACTIVADO
    return _ACTIVADO


def _tipo(respuesta):
    return str((respuesta or {}).get("tipo_respuesta") or "").lower()


def _debe_hablar(respuesta, alcance):
    tipo = _tipo(respuesta)
    if alcance == "todo":
        return True
    if alcance == "acciones":
        return tipo in ("confirmacion", "resultado", "error", "aclaracion")
    # «resumen» es el modo por defecto: habla la versión corta de todo lo que
    # aporta información, incluidas las consultas, sin leer listas completas.
    return tipo in ("confirmacion", "resultado", "consulta", "error", "aclaracion")


def _jugar_bytes(audio):
    if not audio or winsound is None:
        return False
    try:
        # SND_MEMORY exige bytes, no BytesIO. Pasar el buffer lanzaba
        # «TypeError: a bytes-like object is required, not '_io.BytesIO'».
        winsound.PlaySound(audio, winsound.SND_MEMORY)
        return True
    except Exception:  # noqa: BLE001 - plataforma sin audio o WAV invalido
        return False


def _jugar_archivo(path):
    if winsound is None or not path.exists():
        return False
    try:
        winsound.PlaySound(str(path), winsound.SND_FILENAME)
        return True
    except Exception:  # noqa: BLE001 - sin altavoz o archivo incorrecto
        return False


def hablar(client, respuesta, config):
    """Reproduce «respuesta» si la voz está activada."""
    global _ACTIVADO
    _ACTIVADO = bool(config.get("voice_output", True))
    alcance = str(config.get("voice_scope") or "resumen").lower()
    if not _ACTIVADO or not _debe_hablar(respuesta, alcance):
        return False

    if alcance == "resumen":
        mensaje = (respuesta or {}).get("texto_voz") or (respuesta or {}).get(
            "mensaje_nancy"
        )
    else:
        mensaje = (respuesta or {}).get("mensaje_nancy")
    voz = (respuesta or {}).get("voz") or {}
    if voz.get("endpoint") and mensaje:
        try:
            audio = client.synthesize_voice(mensaje)
            if _jugar_bytes(audio):
                return True
        except Exception:  # noqa: BLE001 - sin conexión o backend sin Piper
            pass

    ruta = FRASES.get(_tipo(respuesta))
    return bool(ruta and _jugar_archivo(ruta))
