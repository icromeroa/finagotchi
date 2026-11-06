import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend import ai  # noqa: E402
from test_audio import construir_wav  # noqa: E402


class ProveedorLocalTests(unittest.TestCase):
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

    def test_transcribe_local_sin_texto_da_error(self):
        class Segmento:
            text = "   "

        class Resultado:
            def __iter__(self):
                return iter([Segmento()])

        modelo = mock.MagicMock()
        modelo.transcribe.return_value = (Resultado(), None)

        with mock.patch.object(ai, "_modelo_whisper", return_value=modelo):
            with self.assertRaises(ai.STTSinTexto):
                ai.transcribe_local(construir_wav(2.0))


class SeleccionDeProveedorTests(unittest.TestCase):
    def test_auto_sin_clave_usa_local(self):
        with mock.patch.object(ai, "esta_configurado", return_value=False):
            with mock.patch.object(ai, "local_disponible", return_value=True):
                with mock.patch.object(
                    ai, "transcribe_local", return_value={"texto": "hola"}
                ) as local:
                    resultado = ai.transcribe_audio(construir_wav(1.0))
        local.assert_called_once()
        self.assertEqual(resultado["texto"], "hola")

    def test_auto_sin_clave_sin_local_falla(self):
        with mock.patch.object(ai, "esta_configurado", return_value=False):
            with mock.patch.object(ai, "local_disponible", return_value=False):
                with self.assertRaises(ai.STTNoConfigurado):
                    ai.transcribe_audio(construir_wav(1.0))

    def test_auto_cae_a_local_si_la_clave_es_invalida(self):
        with mock.patch.object(ai, "esta_configurado", return_value=True):
            with mock.patch.object(ai, "local_disponible", return_value=True):
                with mock.patch.object(
                    ai,
                    "transcribe_gemini",
                    side_effect=ai.STTSinPermisos("sin permiso"),
                ):
                    with mock.patch.object(
                        ai,
                        "transcribe_local",
                        return_value={"texto": "hola", "proveedor": "local"},
                    ):
                        resultado = ai.transcribe_audio(construir_wav(1.0))
        self.assertEqual(resultado["proveedor"], "local")
        self.assertEqual(resultado["error_proveedor"], "STT_SIN_PERMISOS")
        self.assertIn("sin permiso", resultado["motivo_fallback"])

    def test_auto_cae_a_local_si_gemini_no_esta_disponible(self):
        with mock.patch.object(ai, "esta_configurado", return_value=True):
            with mock.patch.object(ai, "local_disponible", return_value=True):
                with mock.patch.object(
                    ai,
                    "transcribe_gemini",
                    side_effect=ai.STTNoDisponible("caido"),
                ):
                    with mock.patch.object(
                        ai,
                        "transcribe_local",
                        return_value={"texto": "hola", "proveedor": "local"},
                    ):
                        resultado = ai.transcribe_audio(construir_wav(1.0))
        self.assertEqual(resultado["proveedor"], "local")

    def test_proveedor_explicito_local_no_toca_gemini(self):
        with mock.patch.dict("os.environ", {"STT_PROVEEDOR": "local"}):
            with mock.patch.object(
                ai, "transcribe_local", return_value={"texto": "hola"}
            ) as local:
                with mock.patch.object(ai, "transcribe_gemini") as gemini:
                    ai.transcribe_audio(construir_wav(1.0))
        local.assert_called_once()
        gemini.assert_not_called()

    def test_proveedor_explicito_gemini_no_toca_local(self):
        with mock.patch.dict("os.environ", {"STT_PROVEEDOR": "gemini"}):
            with mock.patch.object(
                ai, "transcribe_gemini", return_value={"texto": "hola"}
            ) as gemini:
                with mock.patch.object(ai, "transcribe_local") as local:
                    ai.transcribe_audio(construir_wav(1.0))
        gemini.assert_called_once()
        local.assert_not_called()


class ClasificacionDeErroresTests(unittest.TestCase):
    def test_401_se_traduce_a_key_invalida(self):
        class Error401(Exception):
            code = 401
            message = "API key not valid."

        with self.assertRaises(ai.STTKeyInvalida) as ctx:
            ai._convertir_error(Error401(), "gemini-3.5-flash")
        self.assertEqual(ctx.exception.detalles["formato_clave"], "AQ")

    def test_403_se_traduce_a_sin_permisos(self):
        class Error403(Exception):
            code = 403
            message = "permission denied"

        with self.assertRaises(ai.STTSinPermisos):
            ai._convertir_error(Error403(), "gemini-3.5-flash")

    def test_429_se_traduce_a_cuota(self):
        class Error429(Exception):
            code = 429
            message = "resource exhausted"

        with self.assertRaises(ai.STTCuota):
            ai._convertir_error(Error429(), "gemini-3.5-flash")

    def test_503_se_traduce_a_no_disponible(self):
        class Error503(Exception):
            code = 503
            message = "unavailable"

        with self.assertRaises(ai.STTNoDisponible):
            ai._convertir_error(Error503(), "gemini-3.5-flash")


if __name__ == "__main__":
    unittest.main()
