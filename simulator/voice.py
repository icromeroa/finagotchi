"""Reproducción de voz en el simulador.

La voz online usa `POST /device/voice/synthesize`; la voz offline usa el banco
de frases pregrabadas en ``simulator/assets/voz``. Si no hay dispositivo de
audio o el backend no tiene Piper, el simulador sigue mostrando el texto.

La reproducción es multiplataforma: ``winsound`` en Windows y ``sounddevice``
en macOS/Linux. Antes solo se usaba ``winsound``, así que en macOS no sonaba
nada aunque el backend generara el WAV.
"""

from pathlib import Path

try:
    import winsound
except Exception:  # noqa: BLE001 - requiere Windows o una API de audio
    winsound = None

try:
    import sounddevice as sd
except Exception:  # noqa: BLE001 - falta PortAudio o no hay tarjeta de audio
    sd = None

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


def _reproducir_con_sounddevice(muestras, sample_rate):
    if sd is None:
        return False
    try:
        sd.play(muestras, sample_rate)
        sd.wait()
        return True
    except Exception:  # noqa: BLE001 - salida de audio no disponible
        return False


def _jugar_bytes(audio):
    if not audio:
        return False
    if winsound is not None:
        try:
            # SND_MEMORY exige bytes, no BytesIO. Pasar el buffer lanzaba
            # «TypeError: a bytes-like object is required, not '_io.BytesIO'».
            winsound.PlaySound(audio, winsound.SND_MEMORY)
            return True
        except Exception:  # noqa: BLE001 - plataforma sin audio o WAV invalido
            pass
    # macOS/Linux (y respaldo de Windows): decodifica el WAV en memoria.
    try:
        import io

        import scipy.io.wavfile as wav

        sample_rate, muestras = wav.read(io.BytesIO(audio))
        return _reproducir_con_sounddevice(muestras, sample_rate)
    except Exception:  # noqa: BLE001 - WAV invalido o sin audio
        return False


def _jugar_archivo(path):
    if not path.exists():
        return False
    if winsound is not None:
        try:
            winsound.PlaySound(str(path), winsound.SND_FILENAME)
            return True
        except Exception:  # noqa: BLE001 - sin altavoz o archivo incorrecto
            pass
    try:
        import scipy.io.wavfile as wav

        sample_rate, muestras = wav.read(str(path))
        return _reproducir_con_sounddevice(muestras, sample_rate)
    except Exception:  # noqa: BLE001 - sin audio o archivo incorrecto
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
