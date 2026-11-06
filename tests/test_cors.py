"""Pruebas de CORS y de la red privada.

Chrome (desde la version 115) envia la cabecera
``Access-Control-Request-Private-Network: true`` cuando una app web le pide
datos a un servidor de la red local. Si el backend no responde con
``Access-Control-Allow-Private-Network: true``, el navegador bloquea la
peticion y esta nunca llega al servidor: la app se ve como si no hubiera
conexion aunque el backend este encendido.
"""

import tempfile
import unittest
from pathlib import Path

from backend.server import create_app


class CorsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app(str(Path(self.temp.name) / "test.db"))
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        self.origen = "http://localhost:52345"

    def tearDown(self):
        self.temp.cleanup()

    def test_preflight_con_red_privada_Lo_permite(self):
        respuesta = self.client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": self.origen,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
                "Access-Control-Request-Private-Network": "true",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.headers.get("Access-Control-Allow-Private-Network"), "true"
        )
        self.assertEqual(respuesta.headers.get("Access-Control-Allow-Origin"), "*")

    def test_preflight_sin_red_privada_no_lo_anade(self):
        respuesta = self.client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": self.origen,
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertIsNone(respuesta.headers.get("Access-Control-Allow-Private-Network"))

    def test_una_peticion_con_origen_recibe_el_permiso(self):
        respuesta = self.client.post(
            "/api/v1/auth/login",
            json={"correo": "nadie@finagotchi.local", "password": "secreto123"},
            headers={"Origin": self.origen},
        )
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.headers.get("Access-Control-Allow-Origin"), "*")

    def test_los_metodos_y_cabeceras_permitidos_siguen_igual(self):
        respuesta = self.client.options(
            "/api/v1/messages",
            headers={
                "Origin": self.origen,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        permitidos = respuesta.headers.get("Access-Control-Allow-Headers", "")
        self.assertIn("Authorization", permitidos)
        self.assertIn("Content-Type", permitidos)


if __name__ == "__main__":
    unittest.main()
