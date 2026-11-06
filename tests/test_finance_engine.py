import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "database"))

import init_db

from backend import finance_engine as fe


class FinanceEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test.db"
        init_db.init_sqlite(self.db_path)
        self.conn = init_db.connect(self.db_path)
        self.user_id = self.create_user()

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def create_user(self, email="ana@example.com"):
        return self.conn.execute(
            "INSERT INTO usuarios (nombre, correo, password_hash) VALUES ('Ana', ?, 'hash')",
            (email,),
        ).lastrowid

    def default_account(self):
        return self.conn.execute(
            "SELECT id FROM cuentas WHERE usuario_id = ? AND es_por_defecto = 1",
            (self.user_id,),
        ).fetchone()[0]

    def income_category(self):
        return self.conn.execute(
            "SELECT id FROM categorias WHERE usuario_id = ? AND tipo = 'ingreso' ORDER BY id LIMIT 1",
            (self.user_id,),
        ).fetchone()[0]

    def expense_category(self):
        return self.conn.execute(
            "SELECT id FROM categorias WHERE usuario_id = ? AND tipo = 'gasto' ORDER BY id LIMIT 1",
            (self.user_id,),
        ).fetchone()[0]

    def add_transaction(self, tipo, amount, fecha_local, categoria_id=None):
        categoria_id = categoria_id or (
            self.income_category() if tipo == "ingreso" else self.expense_category()
        )
        self.conn.execute(
            """
            INSERT INTO transacciones
                (usuario_id, device_uid, secuencia, tipo, monto, categoria_id,
                 cuenta_id, fecha_hora, fecha_local, origen, texto_transcrito,
                 estado, is_deleted)
            VALUES (?, 'DEV-1', 1, ?, ?, ?, ?, ?, ?, 'app_voz', 'texto',
                    'confirmado', 0)
            """,
            (
                self.user_id,
                tipo,
                amount,
                categoria_id,
                self.default_account(),
                fecha_local + "T12:00:00Z",
                fecha_local,
            ),
        )
        self.conn.commit()

    def set_declared_income(self, amount):
        self.conn.execute(
            "UPDATE perfil_financiero SET ingreso_trabajo_mensual = ? WHERE usuario_id = ?",
            (amount, self.user_id),
        )
        self.conn.commit()

    def set_daily_budget(self, amount):
        self.conn.execute(
            "UPDATE usuarios SET presupuesto_diario = ? WHERE id = ?",
            (amount, self.user_id),
        )
        self.conn.commit()

    def add_approved_budget(self, start, end, limite):
        budget_id = self.conn.execute(
            """
            INSERT INTO presupuestos
                (usuario_id, fecha_inicio, fecha_fin, meses, aprobado, aprobado_en)
            VALUES (?, ?, ?, 2, 1, '2026-11-01T12:00:00Z')
            """,
            (self.user_id, start, end),
        ).lastrowid
        self.conn.execute(
            """
            INSERT INTO presupuesto_categoria
                (usuario_id, presupuesto_id, categoria_id, tipo, monto_limite_mensual)
            VALUES (?, ?, ?, 'gasto', ?)
            """,
            (self.user_id, budget_id, self.expense_category(), limite),
        )
        self.conn.commit()

    # --- utilidades de fecha -------------------------------------------------

    def test_date_utilities(self):
        self.assertEqual(fe.parse_date("2026-11-05").isoformat(), "2026-11-05")
        self.assertIsNone(fe.parse_date("no-es-fecha"))
        self.assertEqual(fe.add_months("2026-01-31", 1).isoformat(), "2026-02-28")
        self.assertEqual(fe.add_months("2026-11-05", 3).isoformat(), "2027-02-05")
        self.assertEqual(fe.days_in_month("2028-02-10"), 29)
        self.assertEqual(fe.month_key("2026-11-05"), "2026-11")

    def test_months_until_includes_current_month(self):
        self.assertEqual(fe.months_until("2026-11-30", "2026-11-05"), 1)
        self.assertEqual(fe.months_until("2027-06-30", "2026-11-05"), 8)
        self.assertEqual(fe.months_until("2026-10-31", "2026-11-05"), 0)

    # --- ingreso -------------------------------------------------------------

    def test_declared_income_uses_generated_column(self):
        self.set_declared_income(1500000)
        self.assertEqual(fe.declared_monthly_income(self.conn, self.user_id), 1500000)

    def test_declared_income_zero_is_treated_as_no_data(self):
        self.assertIsNone(fe.declared_monthly_income(self.conn, self.user_id))

    def test_observed_income_is_conservative_over_window(self):
        self.add_transaction("ingreso", 1500000, "2026-10-15")
        observado = fe.observed_monthly_income(self.conn, self.user_id, "2026-11-05")
        self.assertEqual(observado, 500000)

    def test_observed_income_ignores_old_and_unconfirmed_records(self):
        self.add_transaction("ingreso", 900000, "2026-01-10")
        self.assertEqual(
            fe.observed_monthly_income(self.conn, self.user_id, "2026-11-05"), None
        )

    def test_estimate_income_prefers_the_most_conservative_source(self):
        self.set_declared_income(1500000)
        self.add_transaction("ingreso", 2100000, "2026-10-15")
        data = fe.estimate_income(self.conn, self.user_id, "2026-11-05")
        self.assertEqual(data["ingreso_declarado"], 1500000)
        self.assertEqual(data["ingreso_observado"], 700000)
        self.assertEqual(data["ingreso_estimado"], 700000)
        self.assertEqual(data["fuente_ingreso"], "minimo_declarado_observado")

    def test_estimate_income_without_data(self):
        data = fe.estimate_income(self.conn, self.user_id, "2026-11-05")
        self.assertEqual(data["ingreso_estimado"], 0)
        self.assertEqual(data["fuente_ingreso"], "sin_datos")

    # --- gasto ---------------------------------------------------------------

    def test_planned_expense_uses_daily_budget(self):
        self.set_daily_budget(20000)
        data = fe.planned_monthly_expense(self.conn, self.user_id, "2026-11-05")
        self.assertEqual(data["gasto_planificado_mensual"], 600000)
        self.assertEqual(data["fuente_presupuesto"], "presupuesto_diario")

    def test_planned_expense_prefers_approved_monthly_budget(self):
        self.set_daily_budget(20000)
        self.add_approved_budget("2026-11-01", "2026-12-31", 800000)
        data = fe.planned_monthly_expense(self.conn, self.user_id, "2026-11-05")
        self.assertEqual(data["gasto_planificado_mensual"], 800000)
        self.assertEqual(data["fuente_presupuesto"], "presupuesto_mensual")

    def test_planned_expense_without_budget(self):
        self.set_daily_budget(0)
        data = fe.planned_monthly_expense(self.conn, self.user_id, "2026-11-05")
        self.assertEqual(data["gasto_planificado_mensual"], 0)
        self.assertEqual(data["fuente_presupuesto"], "sin_datos")

    # --- capacidad -----------------------------------------------------------

    def test_capacity_prorates_first_month_and_uses_full_months_after(self):
        self.set_declared_income(1500000)
        self.add_transaction("ingreso", 4500000, "2026-10-15")
        self.set_daily_budget(20000)
        data = fe.monthly_capacity(
            self.conn, self.user_id, "2026-11-05", meses=2, colchon_pct=10
        )
        self.assertEqual(data["horizonte_meses"], 2)
        self.assertEqual(data["entradas"]["ingreso_estimado"], 1500000)
        self.assertEqual(data["entradas"]["gasto_planificado_mensual"], 600000)

        primero, segundo = data["capacidad_mensual"]
        self.assertEqual(primero["dias_mes"], 30)
        self.assertEqual(primero["dias_disponibles"], 26)
        self.assertEqual(primero["ingreso_estimado"], 1300000)
        self.assertEqual(primero["gasto_planificado"], 520000)
        self.assertEqual(primero["colchon"], 130000)
        self.assertEqual(primero["capacidad"], 650000)

        self.assertEqual(segundo["dias_disponibles"], 31)
        self.assertEqual(segundo["capacidad"], 750000)

    def test_capacity_is_zero_without_income(self):
        data = fe.monthly_capacity(self.conn, self.user_id, "2026-11-05", meses=3)
        self.assertTrue(all(mes["capacidad"] == 0 for mes in data["capacidad_mensual"]))
        self.assertEqual(data["entradas"]["fuente_ingreso"], "sin_datos")

    def test_capacity_override_applies_to_every_month(self):
        data = fe.monthly_capacity(
            self.conn,
            self.user_id,
            "2026-11-05",
            meses=3,
            capacity_override=250000,
        )
        self.assertEqual(
            [mes["capacidad"] for mes in data["capacidad_mensual"]],
            [250000, 250000, 250000],
        )

    def test_income_and_expense_overrides(self):
        data = fe.monthly_capacity(
            self.conn,
            self.user_id,
            "2026-11-05",
            meses=1,
            colchon_pct=0,
            income_override=1000000,
            expense_override=400000,
        )
        self.assertEqual(data["entradas"]["fuente_ingreso"], "simulacion")
        self.assertEqual(data["entradas"]["fuente_presupuesto"], "simulacion")
        # Noviembre tiene 30 dias y se calcula desde el dia 5: 26/30.
        self.assertEqual(data["capacidad_mensual"][0]["capacidad"], 520000)

    def test_cushion_and_summary(self):
        self.assertEqual(fe.liquidity_cushion(1000000, 10), 100000)
        resumen = fe.summarize_capacity(
            [{"capacidad": 100}, {"capacidad": 300}, {"capacidad": 200}]
        )
        self.assertEqual(resumen["capacidad_total"], 600)
        self.assertEqual(resumen["capacidad_minima"], 100)


if __name__ == "__main__":
    unittest.main()
