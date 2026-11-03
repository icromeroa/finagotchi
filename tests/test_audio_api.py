import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend import ai  # noqa: E402
from backend.db import get_db  # noqa: E402
from backend.server import create_app  # noqa: E402
from test_audio import construir_wav  # noqa: E402


def respuesta_falsa(texto="gasté 14000 en el almuerzo"):
    return {
        "texto": texto,
        "modelo": "gemini-3.5-flash",
        "proveedor": "google",
        "latencia_ms": 1234,
        "tokens_entrada": 100,
        "tokens_salida": 10,
        "idioma": "es-CO",
    }


class AudioApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test.db"
        self.app = create_app(str(self.db_path))
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        self.user = self.register("carla@example.com", "secreto123")

    def tearDown(self):
        self.temp.cleanup()

    def register(self, email, password="secreto123", name="Carla"):
        response = self.client.post(
            "/api/v1/auth/register",
            json={"nombre": name, "correo": email, "password": password},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        payload = response.get_json()["data"]
        return {
            "id": payload["usuario"]["id"],
            "headers": {"Authorization": "Bearer " + payload["tokens"]["access_token"]},
        }

    def post_audio(self, path, wav, headers=None, fields=None):
        data = {"message_id": "msg-audio-1"}
        data.update(fields or {})
        data["audio"] = (io.BytesIO(wav), "audio.wav", "audio/wav")
        return self.client.post(
            path,
            headers=headers or self.user["headers"],
            data=data,
            content_type="multipart/form-data",
        )

    @mock.patch("backend.ai.transcribe_audio")
    def test_audio_valido_genera_mensaje(self, mock_transcribe):
        mock_transcribe.return_value = respuesta_falsa()
        response = self.post_audio("/api/v1/messages", construir_wav(2.0))
        self.assertEqual(response.status_code, 201, response.get_json())
        payload = response.get_json()["data"]
        self.assertEqual(payload["texto_transcrito"], "gasté 14000 en el almuerzo")
        self.assertEqual(payload["intent"], "registrar")
        self.assertEqual(len(payload["transacciones"]), 1)
        self.assertEqual(payload["transacciones"][0]["monto"], 14000)
        self.assertEqual(payload["transacciones"][0]["estado"], "pendiente")
        self.assertAlmostEqual(payload["duracion_audio_s"], 2.0, places=1)

    @mock.patch("backend.ai.transcribe_audio")
    def test_audio_idempotente_no_transcribe_dos_veces(self, mock_transcribe):
        mock_transcribe.return_value = respuesta_falsa()
        primero = self.post_audio("/api/v1/messages", construir_wav(2.0))
        self.assertEqual(primero.status_code, 201, primero.get_json())

        segundo = self.post_audio(
            "/api/v1/messages",
            construir_wav(2.0),
            fields={"message_id": "msg-audio-1"},
        )
        self.assertEqual(segundo.status_code, 200, segundo.get_json())
        self.assertTrue(segundo.get_json()["data"]["duplicado"])
        self.assertEqual(mock_transcribe.call_count, 1)

    @mock.patch("backend.ai.transcribe_audio")
    def test_audio_sin_message_id_es_error(self, mock_transcribe):
        response = self.post_audio(
            "/api/v1/messages", construir_wav(1.0), fields={"message_id": ""}
        )
        self.assertEqual(response.status_code, 422, response.get_json())
        self.assertEqual(response.get_json()["error"]["codigo"], "CAMPOS_REQUERIDOS")
        mock_transcribe.assert_not_called()

    @mock.patch("backend.ai.transcribe_audio")
    def test_audio_con_formato_invalido(self, mock_transcribe):
        response = self.post_audio("/api/v1/messages", construir_wav(1.0, sample_rate=8000))
        self.assertEqual(response.status_code, 422, response.get_json())
        self.assertEqual(response.get_json()["error"]["codigo"], "AUDIO_INVALIDO")
        mock_transcribe.assert_not_called()

    @mock.patch("backend.ai.transcribe_audio")
    def test_audio_muy_largo_es_rechazado(self, mock_transcribe):
        response = self.post_audio("/api/v1/messages", construir_wav(40.5))
        self.assertEqual(response.status_code, 422, response.get_json())
        self.assertEqual(response.get_json()["error"]["codigo"], "AUDIO_INVALIDO")
        mock_transcribe.assert_not_called()

    @mock.patch("backend.ai.transcribe_audio")
    def test_audio_demoracion_maxima_aceptada(self, mock_transcribe):
        mock_transcribe.return_value = respuesta_falsa()
        response = self.post_audio("/api/v1/messages", construir_wav(40.0))
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertAlmostEqual(
            response.get_json()["data"]["duracion_audio_s"], 40.0, places=1
        )

    @mock.patch("backend.ai.transcribe_audio")
    def test_error_del_proveedor_no_crea_mensaje(self, mock_transcribe):
        mock_transcribe.side_effect = ai.STTNoDisponible(
            "El proveedor de transcripcion no esta disponible"
        )
        response = self.post_audio("/api/v1/messages", construir_wav(2.0))
        self.assertEqual(response.status_code, 502, response.get_json())
        self.assertEqual(response.get_json()["error"]["codigo"], "STT_NO_DISPONIBLE")

        with self.app.app_context():
            conn = get_db()
            mensajes = conn.execute(
                "SELECT COUNT(*) FROM mensajes_dispositivo WHERE usuario_id = ?",
                (self.user["id"],),
            ).fetchone()[0]
            self.assertEqual(mensajes, 0)

    @mock.patch("backend.ai.transcribe_audio")
    def test_auditoria_de_ia_registrada(self, mock_transcribe):
        mock_transcribe.return_value = respuesta_falsa()
        response = self.post_audio("/api/v1/messages", construir_wav(2.0))
        self.assertEqual(response.status_code, 201, response.get_json())

        with self.app.app_context():
            conn = get_db()
            row = conn.execute(
                "SELECT * FROM interacciones_ia WHERE usuario_id = ?",
                (self.user["id"],),
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["proveedor"], "google")
            self.assertEqual(row["modelo"], "gemini-3.5-flash")
            self.assertEqual(row["latencia_ms"], 1234)
            self.assertIsNotNone(row["mensaje_id"])
            # La auditoria solo guarda metadatos, nunca el audio.
            self.assertLess(len(row["entrada_json"]), 500)
            self.assertNotIn("base64", row["entrada_json"].lower())
            self.assertNotIn("data", row["entrada_json"].lower())

    @mock.patch("backend.ai.transcribe_audio")
    def test_dispositivo_recibe_audio_y_genera_notificacion(self, mock_transcribe):
        mock_transcribe.return_value = respuesta_falsa()
        device_uid = "esp32-audio-001"
        registration = self.client.post(
            "/api/v1/device/register",
            json={"device_uid": device_uid, "modelo": "ESP32-S3", "firmware": "0.1"},
        )
        pin = registration.get_json()["data"]["pin"]
        paired = self.client.post(
            "/api/v1/device/pair",
            json={"device_uid": device_uid, "pin": pin},
            headers=self.user["headers"],
        )
        device_token = paired.get_json()["data"]["device_token"]
        device_headers = {"X-Device-Token": device_token}

        response = self.post_audio(
            "/api/v1/device/messages",
            construir_wav(3.0),
            headers=device_headers,
            fields={"message_id": "dev-audio-1"},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        message_id = response.get_json()["data"]["id"]

        confirmed = self.client.post(
            f"/api/v1/device/messages/{message_id}/confirm",
            json={},
            headers=device_headers,
        )
        self.assertEqual(confirmed.status_code, 200, confirmed.get_json())
        self.assertEqual(
            confirmed.get_json()["data"]["notificacion"]["tipo"], "movimiento_registrado"
        )

        notifications = self.client.get(
            "/api/v1/device/notifications", headers=device_headers
        )
        rows = notifications.get_json()["data"]["notificaciones"]
        self.assertEqual(len(rows), 1)
        ack = self.client.post(
            f"/api/v1/device/notifications/{rows[0]['id']}/ack",
            json={"estado": "leida"},
            headers=device_headers,
        )
        self.assertEqual(ack.status_code, 200, ack.get_json())

    def test_texto_sigue_funcionando(self):
        response = self.client.post(
            "/api/v1/messages",
            json={"texto": "gasté 12.000 en almuerzo", "message_id": "msg-texto-1"},
            headers=self.user["headers"],
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(response.get_json()["data"]["transacciones"][0]["monto"], 12000)

    def test_sin_audio_ni_texto_es_error(self):
        response = self.client.post(
            "/api/v1/messages", json={"message_id": "msg-vacio"}, headers=self.user["headers"]
        )
        self.assertEqual(response.status_code, 422, response.get_json())
        self.assertEqual(response.get_json()["error"]["codigo"], "CAMPOS_REQUERIDOS")


if __name__ == "__main__":
    unittest.main()
