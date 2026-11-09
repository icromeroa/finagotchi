import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend import ai  # noqa: E402
from test_audio import construir_wav  # noqa: E402


class TranscripcionLocalTests(unittest.TestCase):
    def test_wav_a_float32_desde_bytes(self):
        import numpy as np

        muestras = ai._wav_a_float32(construir_wav(1.0))
        self.assertEqual(muestras.dtype, np.float32)
        self.assertEqual(len(muestras), 16000)
        self.assertLessEqual(float(abs(muestras).max()), 1.0)

    def test_transcribe_local_con_modelo_simulado(self):
        class Segmento:
            text = " gasté 14000 en el almuerzo "

        class Resultado:
            def __iter__(self):
                return iter([Segmento()])

        modelo = mock.MagicMock()
        modelo.transcribe.return_value = (Resultado(), None)

        with mock.patch.object(ai, "_modelo_whisper", return_value=modelo):
            resultado = ai.transcribe_local(construir_wav(2.0))

        self.assertEqual(resultado["texto"], "gasté 14000 en el almuerzo")
        self.assertEqual(resultado["proveedor"], "local")
        self.assertEqual(resultado["modelo"], f"whisper-{ai.modelo_local()}")
        self.assertGreaterEqual(resultado["latencia_ms"], 0)

    def test_transcribe_audio_siempre_usa_local(self):
        with mock.patch.object(
            ai, "transcribe_local", return_value={"texto": "hola"}
        ) as local:
            resultado = ai.transcribe_audio(construir_wav(1.0))
        local.assert_called_once()
        self.assertEqual(resultado["texto"], "hola")

    def test_proveedor_preferido_es_local(self):
        self.assertEqual(ai.proveedor_preferido(), "local")
        self.assertEqual(ai.modelo(), f"whisper-{ai.modelo_local()}")

    def test_sin_local_disponible_falla_claro(self):
        with mock.patch.object(ai, "local_disponible", return_value=False):
            with self.assertRaises(ai.STTNoConfigurado):
                ai.transcribe_audio(construir_wav(1.0))


if __name__ == "__main__":
    unittest.main()
