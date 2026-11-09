import tempfile
import unittest
from pathlib import Path

from backend import conversation  # noqa: E402
from backend.server import create_app


class VinculacionSyncTests(unittest.TestCase):
    def setUp(self):
        conversation.limpiar_sesiones()
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test_vinculacion.db"
        self.app = create_app(str(self.db_path))
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        response = self.client.post(
            "/api/v1/auth/register",
            json={"nombre": "Ana", "correo": "ana@example.com", "password": "secreto123"},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        payload = response.get_json()["data"]
        self.user_token = payload["tokens"]["access_token"]
        self.headers = {"Authorization": "Bearer " + self.user_token}

    def tearDown(self):
        conversation.limpiar_sesiones()
        self.temp.cleanup()

    def test_flujo_pin_flutter_claim_simulador(self):
        device_uid = "FINAGOTCHI-FLUTTER-001"
        # 1. Simulador genera PIN (sin auth)
        registration = self.client.post(
            "/api/v1/device/register",
            json={"device_uid": device_uid, "modelo": "Simulador PC", "firmware": "sim-v3"},
        )
        self.assertEqual(registration.status_code, 201, registration.get_json())
        pin = registration.get_json()["data"]["pin"]
        self.assertEqual(len(pin), 6)

        # 2. Claim antes de pair debe fallar con 409
        claim_antes = self.client.post(
            "/api/v1/device/claim",
            json={"device_uid": device_uid, "pin": pin},
        )
        self.assertEqual(claim_antes.status_code, 409)

        # 3. Flutter vincula con token de usuario
        paired = self.client.post(
            "/api/v1/device/pair",
            json={"device_uid": device_uid, "pin": pin},
            headers=self.headers,
        )
        self.assertEqual(paired.status_code, 200, paired.get_json())
        self.assertIn("device_token", paired.get_json()["data"])

        # 4. Simulador reclama su propio token con el mismo PIN
        claimed = self.client.post(
            "/api/v1/device/claim",
            json={"device_uid": device_uid, "pin": pin},
        )
        self.assertEqual(claimed.status_code, 200, claimed.get_json())
        device_token = claimed.get_json()["data"]["device_token"]
        self.assertTrue(device_token)

        # 5. El token reclamado funciona para enviar movimientos del mismo usuario
        message = self.client.post(
            "/api/v1/device/messages",
            json={"texto": "gasté 8.000 en transporte", "message_id": "sync-msg-1"},
            headers={"X-Device-Token": device_token},
        )
        self.assertEqual(message.status_code, 201, message.get_json())
        message_id = message.get_json()["data"]["id"]
        confirmed = self.client.post(
            f"/api/v1/device/messages/{message_id}/confirm",
            json={},
            headers={"X-Device-Token": device_token},
        )
        self.assertEqual(confirmed.status_code, 200, confirmed.get_json())

        # 6. Flutter (mismo usuario) ve el dispositivo y el movimiento
        devices = self.client.get("/api/v1/device", headers=self.headers)
        self.assertEqual(devices.status_code, 200)
        self.assertEqual(devices.get_json()["data"][0]["device_uid"], device_uid)
        transactions = self.client.get("/api/v1/transactions", headers=self.headers)
        self.assertEqual(transactions.status_code, 200)
        items = transactions.get_json()["data"]["items"]
        self.assertTrue(any(t["monto"] == 8000 for t in items))

    def test_device_home_sin_password_muestra_datos_del_dueno(self):
        device_uid = "FINAGOTCHI-HOME-001"
        registration = self.client.post(
            "/api/v1/device/register",
            json={"device_uid": device_uid},
        )
        pin = registration.get_json()["data"]["pin"]
        self.client.post(
            "/api/v1/device/pair",
            json={"device_uid": device_uid, "pin": pin},
            headers=self.headers,
        )
        claimed = self.client.post(
            "/api/v1/device/claim",
            json={"device_uid": device_uid, "pin": pin},
        )
        device_token = claimed.get_json()["data"]["device_token"]
        device_home = self.client.get(
            "/api/v1/device/home",
            headers={"X-Device-Token": device_token},
        )
        self.assertEqual(device_home.status_code, 200, device_home.get_json())
        self.assertEqual(device_home.get_json()["data"]["usuario"]["nombre"], "Ana")

    def test_claim_pin_invalido_401(self):
        device_uid = "FINAGOTCHI-FLUTTER-001"
        registration = self.client.post(
            "/api/v1/device/register",
            json={"device_uid": device_uid},
        )
        pin_real = registration.get_json()["data"]["pin"]
        self.client.post(
            "/api/v1/device/pair",
            json={"device_uid": device_uid, "pin": pin_real},
            headers=self.headers,
        )
        malo = self.client.post(
            "/api/v1/device/claim",
            json={"device_uid": device_uid, "pin": "000000" if pin_real != "000000" else "999999"},
        )
        self.assertEqual(malo.status_code, 401)


if __name__ == "__main__":
    unittest.main()
