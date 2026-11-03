import io
import unittest
import wave

from backend import audio


def construir_wav(
    duracion_s=1.0,
    sample_rate=audio.SAMPLE_RATE,
    channels=audio.CHANNELS,
    sample_width=audio.SAMPLE_WIDTH,
):
    """Genera un WAV de silencio con los parametros indicados."""
    frames = int(duracion_s * sample_rate)
    if sample_width == 2:
        datos = b"\x00\x00" * frames * channels
    else:
        datos = b"\x00" * frames * channels
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(datos)
    return buffer.getvalue()


class AudioValidationTests(unittest.TestCase):
    def test_wav_valido(self):
        info = audio.validar_wav(construir_wav(2.0))
        self.assertAlmostEqual(info.duracion_s, 2.0, places=2)
        self.assertEqual(info.sample_rate, 16000)
        self.assertEqual(info.channels, 1)
        self.assertEqual(info.sample_width, 2)

    def test_duracion_maxima_40_segundos(self):
        info = audio.validar_wav(construir_wav(40.0))
        self.assertAlmostEqual(info.duracion_s, 40.0, places=2)

    def test_duracion_excede_40_segundos(self):
        with self.assertRaises(audio.AudioInvalido) as ctx:
            audio.validar_wav(construir_wav(40.5))
        self.assertEqual(ctx.exception.detalles["maximo"], 40.0)

    def test_duracion_muy_corta(self):
        with self.assertRaises(audio.AudioInvalido) as ctx:
            audio.validar_wav(construir_wav(0.2))
        self.assertEqual(ctx.exception.detalles["minimo"], 0.5)

    def test_frecuencia_incorrecta(self):
        with self.assertRaises(audio.AudioInvalido) as ctx:
            audio.validar_wav(construir_wav(1.0, sample_rate=8000))
        self.assertEqual(ctx.exception.codigo, "AUDIO_INVALIDO")

    def test_audio_estereo(self):
        with self.assertRaises(audio.AudioInvalido) as ctx:
            audio.validar_wav(construir_wav(1.0, channels=2))
        self.assertEqual(ctx.exception.detalles["channels"], 2)

    def test_bits_incorrectos(self):
        with self.assertRaises(audio.AudioInvalido) as ctx:
            audio.validar_wav(construir_wav(1.0, sample_width=1))
        self.assertEqual(ctx.exception.detalles["sample_width"], 1)

    def test_archivo_vacio(self):
        with self.assertRaises(audio.AudioInvalido):
            audio.validar_wav(b"")

    def test_archivo_que_no_es_wav(self):
        with self.assertRaises(audio.AudioInvalido):
            audio.validar_wav(b"esto no es un archivo de audio")

    def test_archivo_muy_grande(self):
        payload = b"\x00" * (audio.MAX_BYTES + 1)
        with self.assertRaises(audio.AudioMuyGrande) as ctx:
            audio.validar_wav(payload)
        self.assertEqual(ctx.exception.codigo, "AUDIO_MUY_GRANDE")


if __name__ == "__main__":
    unittest.main()
