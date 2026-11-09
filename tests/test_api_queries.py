import tempfile
import unittest
from pathlib import Path

from backend import conversation  # noqa: E402
from backend.server import create_app


class ApiQueriesTestCase(unittest.TestCase):
    def setUp(self):
        conversation.limpiar_sesiones()
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test_api_queries.db"
        self.app = create_app(str(self.db_path))
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        response = self.client.post(
            "/api/v1/auth/register",
            json={"nombre": "Ana", "correo": "ana@example.com", "password": "secreto123"},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        payload = response.get_json()["data"]
        self.headers = {"Authorization": "Bearer " + payload["tokens"]["access_token"]}

    def tearDown(self):
        conversation.limpiar_sesiones()
        self.temp.cleanup()

    def _post_telemetry(self, device_id="FINA-001", sequence=1, measurements=None, message_id=None):
        payload = {
            "device_id": device_id,
            "sequence": sequence,
            "measurements": measurements if measurements is not None else {"temp": 25.5},
        }
        if message_id:
            payload["message_id"] = message_id
        return self.client.post("/api/telemetry", json=payload, headers=self.headers)

    def test_post_telemetry_201_and_listed(self):
        response = self._post_telemetry(message_id="msg-001")
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(response.get_json()["device_id"], "FINA-001")
        self.assertEqual(response.get_json()["measurements"]["temp"], 25.5)

        listed = self.client.get("/api/measurements", headers=self.headers)
        self.assertEqual(listed.status_code, 200)
        items = listed.get_json()
        self.assertIsInstance(items, list)
        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0]["message_id"], "msg-001")
        self.assertEqual(items[0]["sequence"], 1)

    def test_limit_restricts_count(self):
        for index in range(1, 4):
            self._post_telemetry(sequence=index, measurements={"n": index})
        response = self.client.get("/api/measurements?limit=2&offset=0", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 2)

    def test_device_id_filters(self):
        self._post_telemetry(device_id="FINA-001", sequence=1)
        self._post_telemetry(device_id="FINA-002", sequence=1)
        response = self.client.get("/api/measurements?device_id=FINA-001", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        items = response.get_json()
        self.assertTrue(items)
        self.assertTrue(all(item["device_id"] == "FINA-001" for item in items))

    def test_unknown_device_404(self):
        response = self.client.get("/api/devices/NO-EXISTE", headers=self.headers)
        self.assertEqual(response.status_code, 404)

    def test_invalid_limit_422(self):
        for bad in ("limit=0", "limit=500", "limit=abc"):
            response = self.client.get(f"/api/measurements?{bad}", headers=self.headers)
            self.assertEqual(response.status_code, 422, bad)


if __name__ == "__main__":
    unittest.main()
