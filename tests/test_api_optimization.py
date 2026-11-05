import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from backend.server import create_app


class ApiOptimizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test.db"
        self.app = create_app(str(self.db_path))
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        self.user = self.register("optimiza@example.com")
        self.set_income_and_budget()

    def tearDown(self):
        self.temp.cleanup()

    def register(self, email):
        response = self.client.post(
            "/api/v1/auth/register",
            json={"nombre": "Ana", "correo": email, "password": "secreto123"},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        payload = response.get_json()["data"]
        return {
            "id": payload["usuario"]["id"],
            "headers": {"Authorization": "Bearer " + payload["tokens"]["access_token"]},
        }

    def set_income_and_budget(self, income=1500000, daily=20000):
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(
                "UPDATE perfil_financiero SET ingreso_trabajo_mensual = ? WHERE usuario_id = ?",
                (income, self.user["id"]),
            )
            conn.execute(
                "UPDATE usuarios SET presupuesto_diario = ? WHERE id = ?",
                (daily, self.user["id"]),
            )
            conn.commit()

    def get(self, path):
        return self.client.get(path, headers=self.user["headers"])

    def post(self, path, data=None):
        return self.client.post(
            path, json=data or {}, headers=self.user["headers"]
        )

    def create_goal(
        self,
        name="Meta",
        monto=100000,
        prioridad=1,
        limite="2027-06-30",
        aporte=10000,
    ):
        response = self.post(
            "/api/v1/goals",
            {
                "nombre": name,
                "monto_meta": monto,
                "fecha_limite": limite,
                "frecuencia_ahorro": "mensual",
                "aporte_periodico": aporte,
                "prioridad": prioridad,
            },
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["data"]["meta_id"]

    def snapshot(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            return {
                "transacciones": conn.execute(
                    "SELECT COUNT(*) AS n FROM transacciones"
                ).fetchone()["n"],
                "metas": conn.execute("SELECT COUNT(*) AS n FROM metas").fetchone()["n"],
                "salud": conn.execute(
                    "SELECT COUNT(*) AS n FROM salud_log"
                ).fetchone()["n"],
                "filas": [
                    tuple(row)
                    for row in conn.execute(
                        "SELECT id, monto_meta, prioridad, estado FROM metas ORDER BY id"
                    )
                ],
            }

    def test_plan_with_real_data_returns_capacity_and_assignments(self):
        meta_id = self.create_goal(monto=100000, prioridad=5)
        response = self.get(
            "/api/v1/goals/plan?meses=6&fecha=2026-11-05&colchon_pct=10"
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        data = response.get_json()["data"]
        self.assertFalse(data["simulacion"])
        self.assertEqual(data["horizonte_meses"], 6)
        self.assertIn(data["solver"], ("highs", "greedy"))
        self.assertEqual(data["metas"][0]["meta_id"], meta_id)
        self.assertEqual(data["metas"][0]["estado"], "completada")
        self.assertEqual(len(data["capacidad_mensual"]), 6)
        self.assertGreater(data["resumen"]["capacidad_total"], 0)
        self.assertEqual(data["diagnostico"]["codigo"], "METAS_ALCANZABLES")

    def test_plan_does_not_write_any_table(self):
        self.create_goal(monto=500000, prioridad=3)
        before = self.snapshot()
        first = self.get("/api/v1/goals/plan?fecha=2026-11-05")
        second = self.get("/api/v1/goals/plan?fecha=2026-11-05")
        after = self.snapshot()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.get_json()["data"], second.get_json()["data"])
        self.assertEqual(before, after)

    def test_plan_without_goals_is_empty_not_an_error(self):
        response = self.get("/api/v1/goals/plan?fecha=2026-11-05")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]
        self.assertEqual(data["metas"], [])
        self.assertEqual(data["diagnostico"]["codigo"], "SIN_METAS")

    def test_simulation_overrides_capacity_and_priority(self):
        first = self.create_goal(monto=100000, prioridad=1, name="A")
        second = self.create_goal(monto=100000, prioridad=1, name="B")
        response = self.post(
            "/api/v1/goals/plan/simulate",
            {
                "meses": 1,
                "fecha": "2026-11-05",
                "capacidad_mensual": 50000,
                "prioridades": {str(second): 5},
                "incluir_metas": [first, second],
            },
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        data = response.get_json()["data"]
        self.assertTrue(data["simulacion"])
        self.assertEqual(data["overrides"]["capacidad_mensual"], 50000)
        asignadas = {meta["meta_id"]: meta for meta in data["metas"]}
        self.assertEqual(asignadas[first]["total_asignado"], 0)
        self.assertEqual(asignadas[second]["total_asignado"], 50000)

    def test_simulation_with_income_and_expense_overrides(self):
        self.create_goal(monto=100000)
        response = self.post(
            "/api/v1/goals/plan/simulate",
            {
                "fecha": "2026-11-05",
                "meses": 1,
                "ingreso_mensual": 1000000,
                "gasto_mensual": 400000,
                "colchon_pct": 0,
            },
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        data = response.get_json()["data"]
        self.assertEqual(data["entradas"]["fuente_ingreso"], "simulacion")
        self.assertEqual(data["entradas"]["fuente_presupuesto"], "simulacion")
        self.assertEqual(data["capacidad_mensual"][0]["capacidad"], 520000)

    def test_invalid_query_parameters_return_422(self):
        for query in ("meses=0", "meses=25", "colchon_pct=60", "fecha=2026-13-40"):
            response = self.get("/api/v1/goals/plan?" + query)
            self.assertEqual(response.status_code, 422, query)
            payload = response.get_json()
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["codigo"], "PARAMETRO_INVALIDO")

    def test_invalid_simulation_payload_returns_422(self):
        for payload in (
            {"meses": "muchos"},
            {"colchon_pct": -1},
            {"ingreso_mensual": -5},
            {"prioridades": [1, 2]},
            {"prioridades": {"1": 9}},
            {"incluir_metas": "no-es-lista"},
        ):
            response = self.post("/api/v1/goals/plan/simulate", payload)
            self.assertEqual(response.status_code, 422, payload)
            self.assertEqual(
                response.get_json()["error"]["codigo"], "PARAMETRO_INVALIDO"
            )

    def test_foreign_goal_id_is_rejected(self):
        response = self.post(
            "/api/v1/goals/plan/simulate", {"incluir_metas": [999999]}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"]["codigo"], "META_INEXISTENTE")

    def test_goal_priority_is_validated_on_create_and_update(self):
        response = self.post(
            "/api/v1/goals",
            {
                "nombre": "Meta",
                "monto_meta": 100000,
                "fecha_limite": "2027-06-30",
                "frecuencia_ahorro": "mensual",
                "aporte_periodico": 10000,
                "prioridad": 6,
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["error"]["codigo"], "PRIORIDAD_INVALIDA")

        meta_id = self.create_goal()
        update = self.client.patch(
            "/api/v1/goals/{0}".format(meta_id),
            json={"prioridad": 0},
            headers=self.user["headers"],
        )
        self.assertEqual(update.status_code, 422)
        self.assertEqual(update.get_json()["error"]["codigo"], "PRIORIDAD_INVALIDA")

    def test_requires_authentication(self):
        response = self.client.get("/api/v1/goals/plan")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
