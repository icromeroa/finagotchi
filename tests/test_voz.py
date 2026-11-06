"""Pruebas del proveedor local de voz y de su integración con el simulador."""

import io
import os
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

from backend import conversation, tts
from backend.server import create_app


def _wav_minimo():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(22050)
        archivo.writeframes(b"\x00\x00" * 50)
    return buffer.getvalue()


class PiperLocalTests(unittest.TestCase):
    def test_disponible_depende_del_modelo_configurado(self):
        with mock.patch.dict(os.environ, {"PIPER_MODEL": "no-slp-existe.onnx"}, clear=False):
            self.assertFalse(tts.disponible())

    def test_sintetiza_bytes_sin_tocar_disco(self):
        class _VozFalsa:
            def synthesize_wav(self, texto, archivo):
                archivo.setnchannels(1)
                archivo.setsampwidth(2)
                archivo.setframerate(22050)
                archivo.writeframes(b"\x00\x00" * 50)

        with mock.patch.object(tts, "disponible", return_value=True):
            with mock.patch.object(tts, "_voz", return_value=_VozFalsa()):
                audio = tts.sintetizar_wav("Nancy responde en voz")

        self.assertTrue(audio.startswith(b"RIFF"))
        self.assertEqual(audio[8:12], b"WAVE")

    def test_textos_largos_no_pasan(self):
        with mock.patch.object(tts, "disponible", return_value=True):
            self.assertIsNone(tts.sintetizar_wav("x" * (tts.MAX_CARACTERES + 1)))


class IntegracionApiTests(unittest.TestCase):
    def setUp(self):
        conversation.limpiar_sesiones()
        self.temp = tempfile.TemporaryDirectory()
        path = Path(self.temp.name) / "test.db"
        self.app = create_app(str(path))
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        response = self.client.post(
            "/api/v1/auth/register",
            json={"nombre": "Ana", "correo": "ana@example.com", "password": "secreto123"},
        )
        self.headers = {
            "Authorization": "Bearer " + response.get_json()["data"]["tokens"]["access_token"]
        }

    def tearDown(self):
        conversation.limpiar_sesiones()
        try:
            self.temp.cleanup()
        except Exception:  # noqa: BLE001 - Windows puede retrasar el borrado
            pass

    def test_endpoint_devuelve_la_wav_en_solicitud(self):
        with mock.patch.object(tts, "sintetizar_wav", return_value=_wav_minimo()):
            response = self.client.post(
                "/api/v1/voice/synthesize",
                json={"texto": "Hola Nancy"},
                headers=self.headers,
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/wav")
        self.assertTrue(response.data.startswith(b"RIFF"))

    def test_textos_demasiado_largos_se_rechazan(self):
        response = self.client.post(
            "/api/v1/voice/synthesize",
            json={"texto": "x" * (tts.MAX_CARACTERES + 1)},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["error"]["codigo"], "TTS_TEXTO_LARGO")

    def test_sin_sesion_no_sintetiza(self):
        response = self.client.post("/api/v1/voice/synthesize", json={"texto": "Hola"})
        self.assertEqual(response.status_code, 401)

    def test_messages_anuncia_la_voz_si_esta_disponible(self):
        with mock.patch.object(tts, "disponible", return_value=True):
            response = self.client.post(
                "/api/v1/messages",
                json={"texto": "gasté 12.000 en almuerzo", "message_id": "voz-test-1"},
                headers=self.headers,
            )
        self.assertEqual(response.status_code, 201, response.get_json())
        voz = response.get_json()["data"].get("voz") or {}
        self.assertEqual(voz.get("endpoint"), "/api/v1/device/voice/synthesize")


class SimuladorVozTests(unittest.TestCase):
    def setUp(self):
        from simulator import voice

        self.voice = voice
        self.voice.iniciar(True)

    def test_debe_hablar_solo_acciones_por_defecto(self):
        self.assertTrue(self.voice._debe_hablar({"tipo_respuesta": "confirmacion"}, "acciones"))
        self.assertTrue(self.voice._debe_hablar({"tipo_respuesta": "resultado"}, "acciones"))
        self.assertFalse(self.voice._debe_hablar({"tipo_respuesta": "consulta"}, "acciones"))
        self.assertTrue(self.voice._debe_hablar({"tipo_respuesta": "consulta"}, "todo"))

    def test_iniciar_silencia_y_alterna(self):
        self.voice.iniciar(False)
        self.assertFalse(self.voice.activo())
        self.assertTrue(self.voice.alternar())

    def test_hablar_cae_al_banco_pregrabado(self):
        cliente = mock.Mock()
        cliente.synthesize_voice.side_effect = RuntimeError("sin red")
        with mock.patch.object(self.voice, "_jugar_archivo", return_value=True) as jugar:
            resultado = self.voice.hablar(
                cliente,
                {"tipo_respuesta": "resultado", "mensaje_nancy": "resultado dinámico"},
                {"voice_output": True, "voice_scope": "acciones"},
            )
        self.assertTrue(resultado)
        jugar.assert_called_once()

    def test_hablar_no_hace_nada_si_esta_desactivada(self):
        cliente = mock.Mock()
        resultado = self.voice.hablar(
            cliente,
            {"tipo_respuesta": "confirmacion"},
            {"voice_output": False},
        )
        self.assertFalse(resultado)
        cliente.synthesize_voice.assert_not_called()


if __name__ == "__main__":
    unittest.main()
