import unittest

from backend import optimization as opt


def capacities(values, start="2026-11"):
    year, month = (int(part) for part in start.split("-"))
    result = []
    for indice, value in enumerate(values):
        total = month - 1 + indice
        result.append(
            {
                "indice": indice + 1,
                "mes": "{0:04d}-{1:02d}".format(year + total // 12, total % 12 + 1),
                "capacidad": value,
            }
        )
    return result


def goal(meta_id, monto, prioridad=1, limite="2027-06-30", ahorrado=0, nombre=None):
    return {
        "meta_id": meta_id,
        "nombre": nombre or "Meta {0}".format(meta_id),
        "monto_meta": monto,
        "ahorrado": ahorrado,
        "fecha_limite": limite,
        "prioridad": prioridad,
    }


ENTRADAS = {
    "ingreso_estimado": 1000000,
    "fuente_ingreso": "declarado",
    "fuente_presupuesto": "presupuesto_diario",
}


class OptimizationTests(unittest.TestCase):
    def plan(self, metas, caps, **kwargs):
        kwargs.setdefault("entradas", ENTRADAS)
        return opt.plan_goals(metas, caps, "2026-11-05", **kwargs)

    def monthly_totals(self, plan):
        horizon = plan["horizonte_meses"]
        return [
            sum(meta["asignacion_mensual"][mes] for meta in plan["metas"])
            for mes in range(horizon)
        ]

    def test_sufficient_capacity_completes_every_goal(self):
        plan = self.plan(
            [goal(1, 100000), goal(2, 80000)],
            capacities([100000, 100000]),
        )
        self.assertEqual(plan["solver"], "highs")
        self.assertEqual(plan["resumen"]["metas_completadas"], 2)
        self.assertEqual(plan["resumen"]["total_asignado"], 180000)
        self.assertEqual(plan["diagnostico"]["codigo"], "METAS_ALCANZABLES")
        self.assertLessEqual(sum(self.monthly_totals(plan)), 200000)

    def test_scarcity_respects_priority(self):
        plan = self.plan(
            [goal(1, 100000, prioridad=5), goal(2, 100000, prioridad=1)],
            capacities([50000]),
        )
        primera, segunda = plan["metas"]
        self.assertEqual(primera["meta_id"], 1)
        self.assertEqual(primera["total_asignado"], 50000)
        self.assertEqual(primera["estado"], "parcial")
        self.assertEqual(segunda["total_asignado"], 0)
        self.assertEqual(segunda["estado"], "sin_asignacion")
        self.assertGreater(primera["cumplimiento"], segunda["cumplimiento"])
        self.assertEqual(plan["diagnostico"]["codigo"], "CAPACIDAD_LIMITADA")

    def test_no_assignment_after_deadline(self):
        plan = self.plan(
            [goal(1, 100000, limite="2026-11-30")],
            capacities([50000, 50000, 50000, 50000]),
        )
        meta = plan["metas"][0]
        self.assertEqual(meta["meses_disponibles"], 1)
        self.assertEqual(meta["asignacion_mensual"][0], 50000)
        self.assertEqual(meta["asignacion_mensual"][1:], [0, 0, 0])
        self.assertIn("plazo_meta_1", plan["restricciones_activas"])

    def test_expired_goal_receives_nothing(self):
        plan = self.plan(
            [goal(1, 100000, limite="2026-10-31", ahorrado=20000)],
            capacities([50000, 50000]),
        )
        meta = plan["metas"][0]
        self.assertEqual(meta["meses_disponibles"], 0)
        self.assertEqual(meta["total_asignado"], 0)
        self.assertEqual(meta["estado"], "sin_asignacion")
        self.assertEqual(meta["cumplimiento"], 0.2)

    def test_completed_goal_does_not_consume_capacity(self):
        plan = self.plan(
            [goal(1, 100000, ahorrado=120000), goal(2, 50000)],
            capacities([50000]),
        )
        completada, pendiente = plan["metas"]
        self.assertEqual(completada["estado"], "completada")
        self.assertEqual(completada["total_asignado"], 0)
        self.assertEqual(pendiente["total_asignado"], 50000)

    def test_zero_capacity_returns_empty_plan_with_diagnosis(self):
        plan = self.plan([goal(1, 100000)], capacities([0, 0]))
        self.assertEqual(plan["resumen"]["total_asignado"], 0)
        self.assertEqual(plan["diagnostico"]["codigo"], "SIN_CAPACIDAD")

    def test_missing_income_returns_profile_diagnosis(self):
        plan = opt.plan_goals(
            [goal(1, 100000)],
            capacities([0]),
            "2026-11-05",
            entradas={
                "ingreso_estimado": 0,
                "fuente_ingreso": "sin_datos",
                "fuente_presupuesto": "sin_datos",
            },
        )
        self.assertEqual(plan["diagnostico"]["codigo"], "PERFIL_INCOMPLETO")
        self.assertEqual(plan["confianza"], "baja")

    def test_no_goals_is_not_an_error(self):
        plan = self.plan([], capacities([50000]))
        self.assertEqual(plan["metas"], [])
        self.assertEqual(plan["resumen"]["metas_totales"], 0)
        self.assertEqual(plan["diagnostico"]["codigo"], "SIN_METAS")

    def test_rounding_never_exceeds_capacity(self):
        metas = [
            goal(1, 1000),
            goal(2, 1000),
            goal(3, 1000),
        ]
        preparadas = opt._prepare_goals(metas, "2026-11-05", 1)
        raw = {1: {1: 33.33}, 2: {1: 33.33}, 3: {1: 33.34}}
        filas = opt._round_plan(raw, preparadas, [100], 1)
        total = sum(sum(fila) for fila in filas.values())
        self.assertEqual(total, 100)
        for fila in filas.values():
            for value in fila:
                self.assertIsInstance(value, int)

    def test_rounding_respects_per_goal_remaining(self):
        metas = [goal(1, 10)]
        preparadas = opt._prepare_goals(metas, "2026-11-05", 1)
        filas = opt._round_plan({1: {1: 50.0}}, preparadas, [100], 1)
        self.assertEqual(filas[1], [10])

    def test_greedy_fallback_is_valid_and_deterministic(self):
        metas = opt._prepare_goals(
            [goal(1, 100000, prioridad=1), goal(2, 100000, prioridad=5)],
            "2026-11-05",
            3,
        )
        filas = opt._greedy_plan(metas, [50000, 50000, 50000], 3)
        self.assertEqual(filas[2][0], 50000)
        self.assertEqual(filas[1][0], 0)
        segunda = opt._greedy_plan(metas, [50000, 50000, 50000], 3)
        self.assertEqual(filas, segunda)

    def test_plan_is_deterministic(self):
        metas = [goal(1, 90000, 3), goal(2, 70000, 2), goal(3, 50000, 1)]
        caps = capacities([40000, 40000, 40000])
        primero = self.plan(metas, caps)
        segundo = self.plan(metas, caps)
        self.assertEqual(primero, segundo)

    def test_priority_and_goal_overrides_in_simulation(self):
        plan = self.plan(
            [goal(1, 100000, 1), goal(2, 100000, 1)],
            capacities([50000]),
            prioridades={2: 5},
            incluir_metas=[2],
        )
        self.assertEqual(len(plan["metas"]), 1)
        self.assertEqual(plan["metas"][0]["meta_id"], 2)
        self.assertEqual(plan["metas"][0]["prioridad"], 5)
        self.assertEqual(plan["metas"][0]["total_asignado"], 50000)

    def test_weighted_compliance_uses_priority(self):
        plan = self.plan(
            [goal(1, 100000, 5), goal(2, 100000, 1)],
            capacities([50000]),
        )
        # 5 * 0.5 + 1 * 0 sobre un peso total de 6.
        self.assertAlmostEqual(plan["resumen"]["cumplimiento_ponderado"], 0.4167, 4)


if __name__ == "__main__":
    unittest.main()
