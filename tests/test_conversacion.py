"""Pruebas del controlador conversacional y las confirmaciones por voz.

Se usa la API real con una base temporal. El interprete LLM se apaga para que
las pruebas sean deterministas; el respaldo por reglas debe bastar.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from backend import conversation
from backend.server import create_app


class ConversationTests(unittest.TestCase):
    def setUp(self):
        conversation.limpiar_sesiones()
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test.db"
        self.app = create_app(str(self.db_path))
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        self.patch = mock.patch.dict(os.environ, {"NLP_USAR_IA": "off"})
        self.patch.start()
        self.user = self.register("voz@example.com")

    def tearDown(self):
        self.patch.stop()
        conversation.limpiar_sesiones()
        self.temp.cleanup()

    def register(self, email):
        response = self.client.post(
            "/api/v1/auth/register",
            json={"nombre": "Ana", "correo": email, "password": "secreto123"},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        payload = response.get_json()["data"]
        return {"headers": {"Authorization": "Bearer " + payload["tokens"]["access_token"]}}

    def decir(self, texto, message_id=None):
        body = {"texto": texto}
        if message_id:
            body["message_id"] = message_id
        response = self.client.post(
            "/api/v1/messages", json=body, headers=self.user["headers"]
        )
        self.assertIn(response.status_code, (200, 201), response.get_json())
        return response.get_json()["data"]

    def home(self):
        return self.client.get("/api/v1/home", headers=self.user["headers"]).get_json()["data"]

    def crear_meta(self, nombre="Mi nuevo celular", monto=500000):
        response = self.client.post(
            "/api/v1/goals",
            json={
                "nombre": nombre,
                "monto_meta": monto,
                "fecha_limite": "2027-12-31",
                "frecuencia_ahorro": "mensual",
                "aporte_periodico": 50000,
                "prioridad": 3,
            },
            headers=self.user["headers"],
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["data"]

    # --- Confirmaciones -------------------------------------------------
    def test_movimiento_pendiente_y_confirmacion_natural(self):
        respuesta = self.decir("gasté 12.000 en almuerzo", "voz-1")
        self.assertEqual(respuesta["intent"], "registrar")
        self.assertTrue(respuesta["requiere_confirmacion"])
        self.assertEqual(respuesta["estado_conversacion"], "confirmando_movimiento")
        self.assertEqual(respuesta["transacciones"][0]["estado"], "pendiente")
        self.assertIn("¿Está correcto?", respuesta["mensaje_nancy"])

        confirmado = self.decir("sí, está correcto")
        self.assertFalse(confirmado["requiere_confirmacion"])
        self.assertEqual(confirmado["tipo_respuesta"], "resultado")
        self.assertEqual(confirmado["estado_conversacion"], "inactiva")
        self.assertEqual(self.home()["hoy"]["gastos"], 12000)

    def test_confirmacion_con_ok(self):
        self.decir("gasté 20 mil en transporte")
        respuesta = self.decir("ok")
        self.assertEqual(respuesta["tipo_respuesta"], "resultado")
        self.assertEqual(self.home()["hoy"]["gastos"], 20000)

    def test_cancelacion_descarta_el_pendiente(self):
        pendiente = self.decir("gasté 30 mil en comida")
        respuesta = self.decir("no, cancela")
        self.assertEqual(respuesta["tipo_respuesta"], "resultado")
        self.assertEqual(self.home()["hoy"]["gastos"], 0)
        mensaje = self.client.get(
            f"/api/v1/messages/{pendiente['id']}", headers=self.user["headers"]
        ).get_json()["data"]
        self.assertEqual(mensaje["estado"], "descartado")

    def test_correccion_de_monto_antes_de_confirmar(self):
        self.decir("gasté 12.000 en almuerzo")
        correccion = self.decir("cambia el monto a 15 mil")
        self.assertTrue(correccion["requiere_confirmacion"])
        self.assertEqual(correccion["transacciones"][0]["monto"], 15000)
        self.decir("correcto")
        self.assertEqual(self.home()["hoy"]["gastos"], 15000)

    def test_confirmar_sin_pendiente_no_escribe(self):
        respuesta = self.decir("sí")
        self.assertEqual(respuesta["tipo_respuesta"], "aclaracion")
        self.assertIn("nada pendiente", respuesta["mensaje_nancy"])
        self.assertEqual(self.home()["hoy"]["gastos"], 0)

    # --- Metas ----------------------------------------------------------
    def test_ahorro_se_asocia_a_la_meta_del_usuario(self):
        meta = self.crear_meta()
        respuesta = self.decir("ahorré 50 mil para mi meta de mi nuevo celular")
        self.assertEqual(respuesta["transacciones"][0]["tipo"], "ahorro")
        self.assertEqual(respuesta["transacciones"][0]["meta_id"], meta["meta_id"])
        self.assertEqual(respuesta["transacciones"][0]["monto"], 50000)

        self.decir("sí")
        metas = self.client.get("/api/v1/goals", headers=self.user["headers"]).get_json()["data"]
        objetivo = [m for m in metas if m["meta_id"] == meta["meta_id"]][0]
        self.assertEqual(objetivo["ahorrado"], 50000)

    def test_meta_inexistente_pide_aclaracion_sin_escribir(self):
        self.crear_meta(nombre="Viaje")
        respuesta = self.decir("ahorré 50 mil para mi meta de unos audífonos")
        self.assertEqual(respuesta["tipo_respuesta"], "aclaracion")
        self.assertIn("No encontré la meta", respuesta["mensaje_nancy"])
        self.assertEqual(self.home()["hoy"]["ahorro"], 0)

    def test_mensaje_duplicado_no_procesa_dos_veces(self):
        primero = self.decir("gasté 12.000 en almuerzo", "repetido-1")
        segundo = self.decir("otra cosa", "repetido-1")
        self.assertTrue(segundo["duplicado"])
        self.assertEqual(primero["id"], segundo["id"])
        self.assertEqual(self.home()["hoy"]["gastos"], 0)  # sigue pendiente


if __name__ == "__main__":
    unittest.main()
