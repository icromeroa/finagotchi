import tempfile
import unittest
from pathlib import Path

from backend import conversation  # noqa: E402
from backend.db import local_date
from backend.server import create_app


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        conversation.limpiar_sesiones()
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test.db"
        self.app = create_app(str(self.db_path))
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        self.user = self.register("ana@example.com", "secreto123")

    def tearDown(self):
        conversation.limpiar_sesiones()
        self.temp.cleanup()

    def register(self, email, password="secreto123", name="Ana"):
        response = self.client.post(
            "/api/v1/auth/register",
            json={"nombre": name, "correo": email, "password": password},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        payload = response.get_json()["data"]
        return {
            "id": payload["usuario"]["id"],
            "headers": {"Authorization": "Bearer " + payload["tokens"]["access_token"]},
            "refresh": payload["tokens"]["refresh_token"],
        }

    def get(self, path, headers=None):
        return self.client.get(path, headers=headers or self.user["headers"])

    def post(self, path, data=None, headers=None):
        return self.client.post(path, json=data or {}, headers=headers or self.user["headers"])

    def patch(self, path, data=None, headers=None):
        return self.client.patch(path, json=data or {}, headers=headers or self.user["headers"])

    def delete(self, path, data=None, headers=None):
        return self.client.delete(path, json=data or {}, headers=headers or self.user["headers"])

    def test_register_login_me_and_refresh(self):
        login = self.client.post(
            "/api/v1/auth/login",
            json={"correo": "ana@example.com", "password": "secreto123"},
        )
        self.assertEqual(login.status_code, 200, login.get_json())
        refresh = self.client.post(
            "/api/v1/auth/refresh", json={"refresh_token": self.user["refresh"]}
        )
        self.assertEqual(refresh.status_code, 200, refresh.get_json())
        me = self.get("/api/v1/me")
        self.assertEqual(me.status_code, 200, me.get_json())
        self.assertEqual(me.get_json()["data"]["usuario"]["correo"], "ana@example.com")
        self.assertGreaterEqual(me.get_json()["data"]["perfil"]["usuario_id"], 1)

    def test_voice_message_pending_then_confirmed(self):
        message = self.post(
            "/api/v1/messages",
            {"texto": "gasté 12.000 en almuerzo", "message_id": "msg-1"},
        )
        self.assertEqual(message.status_code, 201, message.get_json())
        payload = message.get_json()["data"]
        self.assertEqual(payload["intent"], "registrar")
        self.assertEqual(len(payload["transacciones"]), 1)
        transaction = payload["transacciones"][0]
        self.assertEqual(transaction["estado"], "pendiente")
        self.assertEqual(transaction["monto"], 12000)

        duplicate = self.post(
            "/api/v1/messages",
            {"texto": "otra cosa", "message_id": "msg-1"},
        )
        self.assertEqual(duplicate.status_code, 200, duplicate.get_json())
        self.assertTrue(duplicate.get_json()["data"]["duplicado"])

        confirmed = self.post(f"/api/v1/messages/{payload['id']}/confirm")
        self.assertEqual(confirmed.status_code, 200, confirmed.get_json())
        self.assertEqual(confirmed.get_json()["data"]["puntos_otorgados"], 1)
        self.assertFalse(confirmed.get_json()["data"]["requiere_confirmacion"])

        home = self.get("/api/v1/home")
        self.assertEqual(home.status_code, 200, home.get_json())
        self.assertEqual(home.get_json()["data"]["hoy"]["gastos"], 12000)
        self.assertEqual(home.get_json()["data"]["puntos"], 1)

    def test_close_day_and_metrics(self):
        message = self.post(
            "/api/v1/messages",
            {"texto": "gasté 12.000 en almuerzo", "message_id": "msg-close"},
        ).get_json()["data"]
        pending_close = self.post("/api/v1/days/" + local_date() + "/close")
        self.assertEqual(pending_close.status_code, 400, pending_close.get_json())
        self.post(f"/api/v1/messages/{message['id']}/confirm")

        closed = self.post("/api/v1/days/" + local_date() + "/close")
        self.assertEqual(closed.status_code, 200, closed.get_json())
        data = closed.get_json()["data"]
        self.assertEqual(data["fecha_local"], local_date())
        self.assertIn(data["calificacion"], ("bien", "regular", "mal"))
        self.assertEqual(data["total_gastos"], 12000)
        again = self.post("/api/v1/days/" + local_date() + "/close")
        self.assertEqual(again.status_code, 200, again.get_json())
        self.assertEqual(again.get_json()["data"]["id"], data["id"])

        day = self.get("/api/v1/days/" + local_date())
        self.assertTrue(day.get_json()["data"]["cerrado"])
        health = self.get("/api/v1/metrics/health")
        self.assertIsNotNone(health.get_json()["data"]["persistida"])

    def test_accounts_transactions_and_goals(self):
        accounts = self.get("/api/v1/accounts").get_json()["data"]
        self.assertGreaterEqual(len(accounts), 1)
        categories = self.get("/api/v1/categories?tipo=gasto").get_json()["data"]
        category = categories[0]
        created = self.post(
            "/api/v1/transactions",
            {
                "tipo": "gasto",
                "monto": 5000,
                "categoria_id": category["id"],
                "cuenta_id": accounts[0]["cuenta_id"],
                "concepto": "prueba",
            },
        )
        self.assertEqual(created.status_code, 201, created.get_json())
        transaction_id = created.get_json()["data"]["id"]

        edited = self.patch(
            f"/api/v1/transactions/{transaction_id}", {"monto": 7000, "concepto": "editado"}
        )
        self.assertEqual(edited.status_code, 200, edited.get_json())
        self.assertEqual(edited.get_json()["data"]["monto"], 7000)
        self.assertEqual(edited.get_json()["data"]["version"], 2)

        deleted = self.delete(f"/api/v1/transactions/{transaction_id}")
        self.assertEqual(deleted.status_code, 200, deleted.get_json())
        self.assertTrue(deleted.get_json()["data"]["is_deleted"])
        restored = self.post(f"/api/v1/transactions/{transaction_id}/restore")
        self.assertFalse(restored.get_json()["data"]["is_deleted"])

        goal = self.post(
            "/api/v1/goals",
            {
                "nombre": "Portátil",
                "monto_meta": 2000000,
                "fecha_limite": "2027-06-30",
                "frecuencia_ahorro": "mensual",
                "aporte_periodico": 200000,
            },
        )
        self.assertEqual(goal.status_code, 201, goal.get_json())
        self.assertEqual(goal.get_json()["data"]["nombre"], "Portátil")
        goals = self.get("/api/v1/goals")
        self.assertEqual(goals.status_code, 200, goals.get_json())
        self.assertEqual(len(goals.get_json()["data"]), 1)

    def test_device_pairing_and_message(self):
        device_uid = "esp32-test-001"
        registration = self.client.post(
            "/api/v1/device/register",
            json={"device_uid": device_uid, "modelo": "ESP32-S3", "firmware": "0.1"},
        )
        self.assertEqual(registration.status_code, 201, registration.get_json())
        pin = registration.get_json()["data"]["pin"]
        paired = self.post(
            "/api/v1/device/pair", {"device_uid": device_uid, "pin": pin}
        )
        self.assertEqual(paired.status_code, 200, paired.get_json())
        device_token = paired.get_json()["data"]["device_token"]
        device_headers = {"X-Device-Token": device_token}

        telemetry = self.post(
            "/api/v1/device/telemetry",
            {"bateria": 87, "estado_dispositivo": "reposo", "tipo": "latido"},
            headers=device_headers,
        )
        self.assertEqual(telemetry.status_code, 200, telemetry.get_json())
        self.assertTrue(telemetry.get_json()["data"]["vinculado"])

        message = self.post(
            "/api/v1/device/messages",
            {"texto": "gasté 8.000 en transporte", "message_id": "dev-msg-1"},
            headers=device_headers,
        )
        self.assertEqual(message.status_code, 201, message.get_json())
        message_id = message.get_json()["data"]["id"]
        confirmed = self.post(
            f"/api/v1/device/messages/{message_id}/confirm", {}, headers=device_headers
        )
        self.assertEqual(confirmed.status_code, 200, confirmed.get_json())
        self.assertEqual(confirmed.get_json()["data"]["puntos_otorgados"], 1)
        self.assertEqual(
            confirmed.get_json()["data"]["notificacion"]["tipo"], "movimiento_registrado"
        )

        notifications = self.client.get(
            "/api/v1/device/notifications", headers=device_headers
        )
        self.assertEqual(notifications.status_code, 200, notifications.get_json())
        pending = notifications.get_json()["data"]["notificaciones"]
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["estado"], "pendiente")
        notification_id = pending[0]["id"]

        ack = self.post(
            f"/api/v1/device/notifications/{notification_id}/ack",
            {"estado": "leida"},
            headers=device_headers,
        )
        self.assertEqual(ack.status_code, 200, ack.get_json())
        self.assertEqual(ack.get_json()["data"]["estado"], "leida")
        self.assertIsNotNone(ack.get_json()["data"]["leido_en"])

        empty = self.client.get("/api/v1/device/notifications", headers=device_headers)
        self.assertEqual(empty.get_json()["data"]["notificaciones"], [])

        devices = self.get("/api/v1/device")
        self.assertEqual(devices.status_code, 200, devices.get_json())
        self.assertEqual(devices.get_json()["data"][0]["device_uid"], device_uid)


if __name__ == "__main__":
    unittest.main()
