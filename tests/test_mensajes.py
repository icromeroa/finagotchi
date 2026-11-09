"""Regresion: una propuesta sin monto no puede romper la base.

La tabla de transacciones exige ``monto > 0``. El LLM puede olvidar el monto o
devolver cero: en ese caso la peticion debe degradar a ``requiere_aclaracion``
y no responder con un 500. Se prueba llamando directo a
``services.create_message`` con una propuesta defectuosa.
"""

import tempfile
import unittest
from pathlib import Path

from backend import services
from backend.server import create_app
from database import init_db


class PropuestaSinMontoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test.db"
        self.app = create_app(str(self.db_path))
        self.app.config.update(TESTING=True)
        client = self.app.test_client()
        response = client.post(
            "/api/v1/auth/register",
            json={"nombre": "Ana", "correo": "ana@example.com", "password": "secreto123"},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        self.user_id = response.get_json()["data"]["usuario"]["id"]
        self.conn = init_db.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def test_transaccion_sin_monto_degrada_a_aclaracion(self):
        result = services.create_message(
            self.conn,
            self.user_id,
            "gasté en almuerzo",
            interpretacion={
                "intent": "registrar",
                "transacciones": [
                    {
                        "tipo": "gasto",
                        "monto": None,
                        "categoria_id": 1,
                        "cuenta_id": 1,
                        "concepto": "gasté en almuerzo",
                        "confianza": 0.5,
                    }
                ],
            },
        )
        self.assertEqual(result["intent"], "requiere_aclaracion")
        self.assertEqual(result["transacciones"], [])
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM transacciones WHERE usuario_id = ?", (self.user_id,)
            ).fetchone()[0],
            0,
        )

    def test_propuesta_con_monto_cero_tambien_se_descarta(self):
        result = services.create_message(
            self.conn,
            self.user_id,
            "gasté cero",
            interpretacion={
                "intent": "registrar",
                "transacciones": [
                    {
                        "tipo": "gasto",
                        "monto": 0,
                        "categoria_id": 1,
                        "cuenta_id": 1,
                        "concepto": "gasté cero",
                        "confianza": 0.5,
                    }
                ],
            },
        )
        self.assertEqual(result["intent"], "requiere_aclaracion")

    def test_propuestas_validas_se_conservan_aunque_falte_una(self):
        result = services.create_message(
            self.conn,
            self.user_id,
            "gasté 20 mil en mercado y 5 mil en café",
            interpretacion={
                "intent": "registrar",
                "transacciones": [
                    {
                        "tipo": "gasto",
                        "monto": None,
                        "categoria_id": 1,
                        "cuenta_id": 1,
                        "concepto": "sin monto",
                        "confianza": 0.5,
                    },
                    {
                        "tipo": "gasto",
                        "monto": 5000,
                        "categoria_id": 1,
                        "cuenta_id": 1,
                        "concepto": "con monto",
                        "confianza": 0.9,
                    },
                ],
            },
        )
        self.assertEqual(result["intent"], "registrar")
        self.assertEqual(len(result["transacciones"]), 1)
        self.assertEqual(result["transacciones"][0]["monto"], 5000)


if __name__ == "__main__":
    unittest.main()
