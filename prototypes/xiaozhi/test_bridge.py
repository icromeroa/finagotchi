"""Pruebas del puente Xiaozhi-FinaGotchi.

No necesitan backend real: simulan las respuestas HTTP de FinaGotchi y también
levantan un servidor falso para probar el puente completo en localhost.
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock
from urllib import error, request

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bridge  # noqa: E402


class RespuestaFalsa:
    def __init__(self, estado=200, cuerpo=b"", tipo="application/json", headers=None):
        self.status = estado
        self._cuerpo = cuerpo
        self.headers = headers or {"Content-Type": tipo}

    def read(self):
        return self._cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class NormalizacionTests(unittest.TestCase):
    def test_aplana_el_sobre_data(self):
        respuesta = bridge.normalizar_respuesta(
            {
                "ok": True,
                "data": {
                    "texto_voz": "¿Registro un gasto de 20 mil pesos?",
                    "mensaje_nancy": "¿Registro un gasto de $20.000?",
                    "tipo_respuesta": "confirmacion",
                    "requiere_confirmacion": True,
                    "intent": "registrar",
                    "datos": {"transaccion": {"monto": 20000}},
                },
            }
        )
        self.assertTrue(respuesta["ok"])
        self.assertEqual(respuesta["hablar"], "¿Registro un gasto de 20 mil pesos?")
        self.assertEqual(respuesta["tipo_respuesta"], "confirmacion")
        self.assertTrue(respuesta["requiere_confirmacion"])
        self.assertEqual(respuesta["datos"]["transaccion"]["monto"], 20000)

    def test_hablar_cae_en_mensaje_nancy(self):
        respuesta = bridge.normalizar_respuesta(
            {"ok": True, "data": {"mensaje_nancy": "Listo. Guardé el gasto."}}
        )
        self.assertEqual(respuesta["hablar"], "Listo. Guardé el gasto.")
        self.assertIsNone(respuesta["texto_voz"])

    def test_error_de_finagotchi_se_conserva(self):
        respuesta = bridge.normalizar_respuesta(
            {
                "ok": False,
                "error": {"codigo": "DISPOSITIVO_NO_VINCULADO", "mensaje": "Sin dueño"},
            }
        )
        self.assertFalse(respuesta["ok"])
        self.assertEqual(respuesta["error"]["codigo"], "DISPOSITIVO_NO_VINCULADO")
        self.assertIn("no pudo procesar", respuesta["hablar"])

    def test_texto_de_sintesis_acepta_alias(self):
        self.assertEqual(bridge.texto_de_sintesis({"texto": "hola"}), "hola")
        self.assertEqual(bridge.texto_de_sintesis({"prompt_text": "hola"}), "hola")
        self.assertEqual(bridge.texto_de_sintesis({"input": "hola"}), "hola")
        self.assertEqual(bridge.texto_de_sintesis({"text": "hola"}), "hola")
        self.assertEqual(bridge.texto_de_sintesis({}), "")


class ConfigTests(unittest.TestCase):
    def test_entorno_gana_sobre_archivo(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "config.json"
            ruta.write_text(
                json.dumps(
                    {
                        "finagotchi_base_url": "http://archivo/api/v1",
                        "device_token": "token-archivo",
                        "bridge_port": 9000,
                    }
                ),
                encoding="utf-8",
            )
            config = bridge.cargar_config(
                ruta,
                entorno={
                    "FINAGOTCHI_DEVICE_TOKEN": "token-entorno",
                    "XIAOZHI_BRIDGE_PORT": "9100",
                },
            )
        self.assertEqual(config["finagotchi_base_url"], "http://archivo/api/v1")
        self.assertEqual(config["device_token"], "token-entorno")
        self.assertEqual(config["bridge_port"], 9100)

    def test_defaults_sin_archivo(self):
        with tempfile.TemporaryDirectory() as carpeta:
            config = bridge.cargar_config(Path(carpeta) / "no-existe.json", entorno={})
        self.assertEqual(config["finagotchi_base_url"], bridge.DEFAULT_BASE_URL)
        self.assertEqual(config["bridge_port"], bridge.DEFAULT_PORT)
        self.assertEqual(config["device_token"], "")


class ClienteFinaGotchiTests(unittest.TestCase):
    def setUp(self):
        self.cliente = bridge.ClienteFinaGotchi(
            "http://finagotchi.local/api/v1", "token-secreto"
        )

    def test_turno_envia_token_y_message_id(self):
        capturado = {}

        def falso_urlopen(peticion, timeout=None):
            capturado["url"] = peticion.full_url
            capturado["token"] = peticion.headers.get("X-device-token")
            capturado["cuerpo"] = json.loads(peticion.data.decode("utf-8"))
            return RespuestaFalsa(
                cuerpo=json.dumps(
                    {
                        "ok": True,
                        "data": {
                            "texto_voz": "¿Registro un gasto de 20 mil pesos?",
                            "mensaje_nancy": "¿Registro un gasto de $20.000?",
                            "tipo_respuesta": "confirmacion",
                            "requiere_confirmacion": True,
                        },
                    }
                ).encode("utf-8")
            )

        with mock.patch.object(bridge.request, "urlopen", falso_urlopen):
            estado, respuesta = self.cliente.turno("gasté 20 mil en almuerzo")

        self.assertEqual(estado, 200)
        self.assertTrue(respuesta["ok"])
        self.assertEqual(respuesta["hablar"], "¿Registro un gasto de 20 mil pesos?")
        self.assertEqual(capturado["url"], "http://finagotchi.local/api/v1/device/messages")
        self.assertEqual(capturado["token"], "token-secreto")
        self.assertTrue(capturado["cuerpo"]["message_id"].startswith("xiaozhi-"))
        self.assertEqual(capturado["cuerpo"]["texto"], "gasté 20 mil en almuerzo")

    def test_turno_respeta_message_id_explicito(self):
        capturado = {}

        def falso_urlopen(peticion, timeout=None):
            capturado["cuerpo"] = json.loads(peticion.data.decode("utf-8"))
            return RespuestaFalsa(cuerpo=b'{"ok": true, "data": {"mensaje_nancy": "ok"}}')

        with mock.patch.object(bridge.request, "urlopen", falso_urlopen):
            self.cliente.turno("hola", message_id="fijo-123")

        self.assertEqual(capturado["cuerpo"]["message_id"], "fijo-123")

    def test_sintetizar_devuelve_bytes(self):
        capturado = {}

        def falso_urlopen(peticion, timeout=None):
            capturado["url"] = peticion.full_url
            capturado["cuerpo"] = json.loads(peticion.data.decode("utf-8"))
            return RespuestaFalsa(cuerpo=b"RIFF....WAVE", tipo="audio/wav")

        with mock.patch.object(bridge.request, "urlopen", falso_urlopen):
            estado, tipo, audio = self.cliente.sintetizar("¿Registro?")

        self.assertEqual(estado, 200)
        self.assertEqual(tipo, "audio/wav")
        self.assertEqual(audio, b"RIFF....WAVE")
        self.assertTrue(capturado["url"].endswith("/device/voice/synthesize"))
        self.assertEqual(capturado["cuerpo"]["texto"], "¿Registro?")

    def test_error_http_se_reenvia(self):
        def falso_urlopen(peticion, timeout=None):
            raise error.HTTPError(
                peticion.full_url,
                422,
                "Unprocessable",
                {"Content-Type": "application/json"},
                io.BytesIO(
                    json.dumps(
                        {
                            "ok": False,
                            "error": {"codigo": "CAMPOS_REQUERIDOS", "mensaje": "Falta texto"},
                        }
                    ).encode("utf-8")
                ),
            )

        with mock.patch.object(bridge.request, "urlopen", falso_urlopen):
            estado, respuesta = self.cliente.turno("hola")

        self.assertEqual(estado, 422)
        self.assertFalse(respuesta["ok"])
        self.assertEqual(respuesta["error"]["codigo"], "CAMPOS_REQUERIDOS")

    def test_sin_token_falla_claro(self):
        cliente = bridge.ClienteFinaGotchi("http://finagotchi.local/api/v1", "")
        with self.assertRaises(bridge.ErrorPuente):
            cliente.turno("hola")


class FakeFinaGotchi(BaseHTTPRequestHandler):
    def do_POST(self):
        largo = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(largo)
        if self.path.endswith("/device/messages"):
            cuerpo = {
                "ok": True,
                "data": {
                    "texto_voz": "¿Registro un gasto de 20 mil pesos en almuerzo?",
                    "mensaje_nancy": "¿Registro un gasto de $20.000 en Alimentación?",
                    "tipo_respuesta": "confirmacion",
                    "requiere_confirmacion": True,
                    "intent": "registrar",
                    "datos": {"transaccion": {"monto": 20000}},
                },
            }
            self._json(200, cuerpo)
            return
        if self.path.endswith("/device/voice/synthesize"):
            audio = b"RIFF\x00\x00\x00\x00WAVEfmt "
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(audio)))
            self.end_headers()
            self.wfile.write(audio)
            return
        self._json(404, {"ok": False, "error": {"codigo": "NO_ENCONTRADO"}})

    def _json(self, estado, payload):
        cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, formato, *args):
        pass


class PuenteCompletoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake = ThreadingHTTPServer(("127.0.0.1", 0), FakeFinaGotchi)
        cls.hilo_fake = threading.Thread(target=cls.fake.serve_forever, daemon=True)
        cls.hilo_fake.start()

        base = f"http://127.0.0.1:{cls.fake.server_address[1]}/api/v1"
        config = {
            "finagotchi_base_url": base,
            "device_token": "token-de-prueba",
            "bridge_host": "127.0.0.1",
            "bridge_port": 0,
            "timeout_s": 10,
        }
        cls.puente = bridge.crear_servidor(config)
        cls.hilo_puente = threading.Thread(target=cls.puente.serve_forever, daemon=True)
        cls.hilo_puente.start()
        cls.bridge_url = f"http://127.0.0.1:{cls.puente.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.puente.shutdown()
        cls.puente.server_close()
        cls.fake.shutdown()
        cls.fake.server_close()
        cls.hilo_puente.join(timeout=2)
        cls.hilo_fake.join(timeout=2)

    def _post(self, ruta, payload):
        cuerpo = json.dumps(payload).encode("utf-8")
        peticion = request.Request(
            self.bridge_url + ruta,
            data=cuerpo,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(peticion, timeout=10) as respuesta:
                return (
                    respuesta.status,
                    respuesta.headers.get("Content-Type", ""),
                    respuesta.read(),
                )
        except error.HTTPError as exc:
            try:
                raise
            finally:
                exc.close()

    def test_turno_completo(self):
        estado, _tipo, cuerpo = self._post("/turno", {"texto": "gasté 20 mil en almuerzo"})
        datos = json.loads(cuerpo.decode("utf-8"))
        self.assertEqual(estado, 200)
        self.assertTrue(datos["ok"])
        self.assertIn("20 mil pesos", datos["hablar"])
        self.assertIn("$20.000", datos["mensaje_nancy"])
        self.assertTrue(datos["requiere_confirmacion"])

    def test_sintetizar_completo(self):
        estado, tipo, audio = self._post("/sintetizar", {"prompt_text": "hola"})
        self.assertEqual(estado, 200)
        self.assertIn("audio/wav", tipo)
        self.assertTrue(audio.startswith(b"RIFF"))

    def test_salud(self):
        with request.urlopen(self.bridge_url + "/salud", timeout=10) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
        self.assertTrue(datos["ok"])
        self.assertTrue(datos["token_configurado"])
        self.assertEqual(datos["servicio"], "puente-xiaozhi-finagotchi")

    def test_ruta_desconocida(self):
        with self.assertRaises(error.HTTPError) as contexto:
            self._post("/no-existe", {})
        self.assertEqual(contexto.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
