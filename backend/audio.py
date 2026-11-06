"""Validacion del audio WAV que envia el dispositivo o la app.

El backend no interpreta el audio: solo comprueba que cumple el contrato
acordado (WAV, 16 kHz, mono, 16 bits, entre 0.5 y 40 segundos) y calcula la
duracion real en el servidor. El archivo nunca se escribe en disco.
"""

import io
import wave

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2
MIN_DURACION_S = 0.5
MAX_DURACION_S = 40.0
MAX_BYTES = 2 * 1024 * 1024
MIME_TYPE = "audio/wav"


class AudioInvalido(ValueError):
    """El audio no cumple el formato acordado."""

    codigo = "AUDIO_INVALIDO"

    def __init__(self, mensaje, detalles=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalles = detalles or {}


class AudioMuyGrande(AudioInvalido):
    """El audio supera el tamano maximo permitido."""

    codigo = "AUDIO_MUY_GRANDE"


class AudioInfo:
    """Datos del audio validado."""

    def __init__(self, duracion_s, bytes_total, sample_rate, channels, sample_width, frames):
        self.duracion_s = duracion_s
        self.bytes_total = bytes_total
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width
        self.frames = frames

    def as_dict(self):
        return {
            "duracion_s": round(self.duracion_s, 3),
            "bytes": self.bytes_total,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width": self.sample_width,
            "frames": self.frames,
        }


def validar_wav(audio_bytes):
    """Valida un WAV y devuelve un AudioInfo.

    Lanza AudioMuyGrande si el archivo excede MAX_BYTES y AudioInvalido si el
    formato o la duracion no cumplen el contrato.
    """
    if not audio_bytes:
        raise AudioInvalido("El archivo de audio esta vacio")

    if len(audio_bytes) > MAX_BYTES:
        raise AudioMuyGrande(
            "El audio supera el tamano maximo permitido",
            {"bytes": len(audio_bytes), "max_bytes": MAX_BYTES},
        )

    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            frames = wav_file.getnframes()
    except wave.Error as exc:
        raise AudioInvalido(
            "El archivo no es un WAV valido", {"detalle": str(exc)}
        ) from exc
    except EOFError as exc:
        raise AudioInvalido("El archivo WAV esta incompleto") from exc

    if channels != CHANNELS:
        raise AudioInvalido(
            "El audio debe ser mono",
            {"channels": channels, "esperado": CHANNELS},
        )
    if sample_width != SAMPLE_WIDTH:
        raise AudioInvalido(
            "El audio debe ser de 16 bits",
            {"sample_width": sample_width, "esperado": SAMPLE_WIDTH},
        )
    if sample_rate != SAMPLE_RATE:
        raise AudioInvalido(
            "El audio debe estar muestreado a 16 kHz",
            {"sample_rate": sample_rate, "esperado": SAMPLE_RATE},
        )

    duration = frames / float(sample_rate) if sample_rate else 0.0
    if duration < MIN_DURACION_S:
        raise AudioInvalido(
            "El audio es demasiado corto",
            {"duracion_s": round(duration, 3), "minimo": MIN_DURACION_S},
        )
    if duration > MAX_DURACION_S:
        raise AudioInvalido(
            "El audio supera la duracion maxima",
            {"duracion_s": round(duration, 3), "maximo": MAX_DURACION_S},
        )

    return AudioInfo(
        duracion_s=duration,
        bytes_total=len(audio_bytes),
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width,
        frames=frames,
    )
