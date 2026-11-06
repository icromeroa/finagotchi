import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "database"))

import init_db


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test.db"
        init_db.init_sqlite(self.db_path)
        self.conn = init_db.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def create_user(self, email="ana@example.com", name="Ana"):
        return self.conn.execute(
            "INSERT INTO usuarios (nombre, correo, password_hash) VALUES (?, ?, 'hash')",
            (name, email),
        ).lastrowid

    def default_account(self, user_id):
        return self.conn.execute(
            "SELECT id FROM cuentas WHERE usuario_id = ? AND es_por_defecto = 1",
            (user_id,),
        ).fetchone()[0]

    def first_category(self, user_id, tipo="gasto"):
        return self.conn.execute(
            "SELECT id FROM categorias WHERE usuario_id = ? AND tipo = ? ORDER BY id LIMIT 1",
            (user_id, tipo),
        ).fetchone()[0]

    def message(self, user_id, message_id="m1", text="gaste 10000 en almuerzo"):
        return self.conn.execute(
            """
            INSERT INTO mensajes_dispositivo
                (usuario_id, device_uid, message_id, texto_transcrito)
            VALUES (?, 'DEV-1', ?, ?)
            """,
            (user_id, message_id, text),
        ).lastrowid

    def transaction(
        self,
        user_id,
        category_id,
        amount=10000,
        tipo="gasto",
        state="confirmado",
        message_id=None,
        account_id=None,
        local_date="2026-11-02",
        sequence=1,
    ):
        account_id = account_id or self.default_account(user_id)
        return self.conn.execute(
            """
            INSERT INTO transacciones
                (usuario_id, mensaje_id, device_uid, secuencia, tipo, monto,
                 categoria_id, cuenta_id, fecha_hora, fecha_local, origen,
                 texto_transcrito, estado)
            VALUES (?, ?, 'DEV-1', ?, ?, ?, ?, ?, ?, ?, 'app_voz', 'texto', ?)
            """,
            (
                user_id,
                message_id,
                sequence,
                tipo,
                amount,
                category_id,
                account_id,
                local_date + "T12:00:00Z",
                local_date,
                state,
            ),
        ).lastrowid

    def test_schema_version_and_catalogs(self):
        self.assertEqual(init_db.schema_version(self.conn), 4)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM plantilla_categorias").fetchone()[0], 16
        )
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM plantilla_cuentas").fetchone()[0], 5
        )
        self.assertEqual(self.conn.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_user_seed_is_complete(self):
        user_id = self.create_user()
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM categorias WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0],
            16,
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM cuentas WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0],
            5,
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM perfil_secciones WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0],
            6,
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT salud FROM estado_mascota WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0],
            100,
        )

    def test_one_message_many_transactions(self):
        user_id = self.create_user()
        category_id = self.first_category(user_id)
        message_id = self.message(user_id)
        self.transaction(user_id, category_id, amount=10000, message_id=message_id, sequence=1)
        self.transaction(user_id, category_id, amount=3000, message_id=message_id, sequence=2)
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM transacciones WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0],
            2,
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT puntos_totales FROM v_puntos_usuario WHERE usuario_id = ?",
                (user_id,),
            ).fetchone()[0],
            2,
        )

    def test_duplicate_message_is_rejected(self):
        user_id = self.create_user()
        self.message(user_id, "same")
        with self.assertRaises(sqlite3.IntegrityError):
            self.message(user_id, "same")

    def test_pending_does_not_affect_balance_or_points(self):
        user_id = self.create_user()
        category_id = self.first_category(user_id)
        self.transaction(user_id, category_id, amount=10000, state="pendiente")
        self.assertIsNone(
            self.conn.execute(
                "SELECT * FROM v_balance_diario WHERE usuario_id = ?", (user_id,)
            ).fetchone()
        )
        self.assertIsNone(
            self.conn.execute(
                "SELECT * FROM v_puntos_usuario WHERE usuario_id = ?", (user_id,)
            ).fetchone()
        )

    def test_annulled_and_restored_transaction(self):
        user_id = self.create_user()
        category_id = self.first_category(user_id)
        tx_id = self.transaction(user_id, category_id, amount=10000)
        self.conn.execute(
            """
            UPDATE transacciones
               SET is_deleted = 1,
                   deleted_at = '2026-11-02T12:10:00Z',
                   eliminado_via = 'app'
             WHERE id = ?
            """,
            (tx_id,),
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM v_movimientos WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0],
            0,
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM v_papelera WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0],
            1,
        )
        self.conn.execute(
            """
            UPDATE transacciones
               SET is_deleted = 0,
                   deleted_at = NULL,
                   eliminado_via = NULL
             WHERE id = ?
            """,
            (tx_id,),
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM v_movimientos WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0],
            1,
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT puntos_totales FROM v_puntos_usuario WHERE usuario_id = ?",
                (user_id,),
            ).fetchone()[0],
            1,
        )

    def test_only_one_default_account(self):
        user_id = self.create_user()
        account_id = self.conn.execute(
            "SELECT id FROM cuentas WHERE usuario_id = ? AND es_por_defecto = 0 LIMIT 1",
            (user_id,),
        ).fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "UPDATE cuentas SET es_por_defecto = 1 WHERE id = ?", (account_id,)
            )

    def test_default_account_cannot_be_hidden(self):
        user_id = self.create_user()
        account_id = self.default_account(user_id)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "UPDATE cuentas SET oculta = 1 WHERE id = ?", (account_id,)
            )

    def test_system_category_cannot_be_renamed(self):
        user_id = self.create_user()
        category_id = self.first_category(user_id)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "UPDATE categorias SET nombre = 'Otra' WHERE id = ?", (category_id,)
            )

    def test_mood_values(self):
        user_id = self.create_user()
        for health, mood in [(100, "FELIZ"), (80, "PREOCUPADO"), (50, "TRISTE"), (20, "CRITICO")]:
            self.conn.execute(
                "UPDATE estado_mascota SET salud = ? WHERE usuario_id = ?",
                (health, user_id),
            )
            result = self.conn.execute(
                "SELECT animo FROM v_estado_mascota WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0]
            self.assertEqual(result, mood)

    def test_user_isolation_in_foreign_keys(self):
        user_a = self.create_user("a@example.com", "A")
        user_b = self.create_user("b@example.com", "B")
        account_a = self.default_account(user_a)
        category_b = self.first_category(user_b)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO transacciones
                    (usuario_id, tipo, monto, categoria_id, cuenta_id,
                     fecha_hora, fecha_local, origen, estado)
                VALUES (?, 'gasto', 10000, ?, ?, '2026-11-02T12:00:00Z',
                        '2026-11-02', 'manual', 'confirmado')
                """,
                (user_a, category_b, account_a),
            )

    def test_health_log_delta(self):
        user_id = self.create_user()
        log_id = self.conn.execute(
            """
            INSERT INTO salud_log
                (usuario_id, fecha_local, regla_codigo, motivo,
                 salud_anterior, salud_nueva, referencia_tipo)
            VALUES (?, '2026-11-02', 'EXCESO_DIARIO', 'presupuesto_diario', 100, 80, 'cierre')
            """,
            (user_id,),
        ).lastrowid
        delta = self.conn.execute(
            "SELECT delta FROM salud_log WHERE id = ?", (log_id,)
        ).fetchone()[0]
        self.assertEqual(delta, -20)

    def test_closure_snapshot(self):
        user_id = self.create_user()
        self.conn.execute(
            """
            INSERT INTO cierres_dia
                (usuario_id, fecha_local, total_ingresos, total_gastos,
                 total_ahorrado, balance_neto, presupuesto_diario,
                 porcentaje_usado, calificacion, num_registros,
                 salud_inicio, salud_fin)
            VALUES (?, '2026-11-02', 50000, 30000, 0, 20000, 30000, 100,
                    'bien', 2, 100, 90)
            """,
            (user_id,),
        )
        row = self.conn.execute(
            "SELECT delta_salud FROM cierres_dia WHERE usuario_id = ?", (user_id,)
        ).fetchone()
        self.assertEqual(row[0], -10)

    def test_goal_progress(self):
        user_id = self.create_user()
        category_id = self.first_category(user_id)
        meta_id = self.conn.execute(
            """
            INSERT INTO metas
                (usuario_id, nombre, monto_meta, fecha_limite,
                 frecuencia_ahorro, aporte_periodico)
            VALUES (?, 'Viaje', 100000, '2026-12-31', 'semanal', 10000)
            """,
            (user_id,),
        ).lastrowid
        self.transaction(
            user_id,
            None,
            amount=25000,
            tipo="ahorro",
            message_id=None,
        )
        self.conn.execute(
            "UPDATE transacciones SET categoria_id = NULL, meta_id = ? WHERE id = last_insert_rowid()",
            (meta_id,),
        )
        row = self.conn.execute(
            "SELECT ahorrado, faltante FROM v_metas_progreso WHERE meta_id = ?",
            (meta_id,),
        ).fetchone()
        self.assertEqual(row[0], 25000)
        self.assertEqual(row[1], 75000)

    def test_goal_expected_uses_scheduled_contributions(self):
        user_id = self.create_user()
        meta_id = self.conn.execute(
            """
            INSERT INTO metas
                (usuario_id, nombre, monto_meta, fecha_limite,
                 frecuencia_ahorro, aporte_periodico, creado_en)
            VALUES (?, 'Viaje', 100000, date('now', '-5 hours', '+30 days'),
                    'semanal', 10000, date('now', '-5 hours', '-30 days') || 'T12:00:00Z')
            """,
            (user_id,),
        ).lastrowid
        row = self.conn.execute(
            "SELECT esperado, estado_plan FROM v_metas_estado WHERE meta_id = ?",
            (meta_id,),
        ).fetchone()
        self.assertEqual(row[0], 40000)
        self.assertEqual(row[1], "atrasada")

        tx_id = self.transaction(user_id, None, amount=40000, tipo="ahorro")
        self.conn.execute(
            "UPDATE transacciones SET meta_id = ? WHERE id = ?", (meta_id, tx_id)
        )
        row = self.conn.execute(
            "SELECT ahorrado, esperado, estado_plan FROM v_metas_estado WHERE meta_id = ?",
            (meta_id,),
        ).fetchone()
        self.assertEqual(row[0], 40000)
        self.assertEqual(row[1], 40000)
        self.assertEqual(row[2], "vas_bien")

        tx_id = self.transaction(user_id, None, amount=60000, tipo="ahorro")
        self.conn.execute(
            "UPDATE transacciones SET meta_id = ? WHERE id = ?", (meta_id, tx_id)
        )
        row = self.conn.execute(
            "SELECT estado_plan FROM v_metas_estado WHERE meta_id = ?",
            (meta_id,),
        ).fetchone()
        self.assertEqual(row[0], "completada")

    def test_goal_expected_is_capped_by_target(self):
        user_id = self.create_user()
        meta_id = self.conn.execute(
            """
            INSERT INTO metas
                (usuario_id, nombre, monto_meta, fecha_limite,
                 frecuencia_ahorro, aporte_periodico, creado_en)
            VALUES (?, 'Audifonos', 30000, date('now', '-5 hours', '+30 days'),
                    'semanal', 10000, date('now', '-5 hours', '-30 days') || 'T12:00:00Z')
            """,
            (user_id,),
        ).lastrowid
        row = self.conn.execute(
            "SELECT esperado FROM v_metas_estado WHERE meta_id = ?",
            (meta_id,),
        ).fetchone()
        self.assertEqual(row[0], 30000)

    def test_device_factory_reset(self):
        user_id = self.create_user()
        device_id = self.conn.execute(
            """
            INSERT INTO dispositivos
                (device_uid, usuario_id, token_hash, vinculado_en, estado_conexion)
            VALUES ('DEVICE-1', ?, 'hash', '2026-11-02T12:00:00Z', 'conectado')
            """,
            (user_id,),
        ).lastrowid
        self.conn.execute("UPDATE dispositivos SET usuario_id = NULL WHERE id = ?", (device_id,))
        row = self.conn.execute(
            "SELECT usuario_id, token_hash, estado_conexion FROM dispositivos WHERE id = ?",
            (device_id,),
        ).fetchone()
        self.assertIsNone(row[0])
        self.assertIsNone(row[1])
        self.assertEqual(row[2], "desconectado")

    def test_device_notification_queue(self):
        user_id = self.create_user()
        category_id = self.first_category(user_id)
        message_id = self.message(user_id)
        transaction_id = self.transaction(user_id, category_id, message_id=message_id)
        device_id = self.conn.execute(
            """
            INSERT INTO dispositivos
                (device_uid, usuario_id, token_hash, vinculado_en, estado_conexion)
            VALUES ('DEVICE-2', ?, 'hash', '2026-11-02T12:00:00Z', 'conectado')
            """,
            (user_id,),
        ).lastrowid
        notification_id = self.conn.execute(
            """
            INSERT INTO dispositivos_notificaciones
                (dispositivo_id, usuario_id, mensaje_id, transaccion_id,
                 tipo, titulo, mensaje)
            VALUES (?, ?, ?, ?, 'movimiento_registrado',
                    'Registro guardado', 'Se guardo el movimiento')
            """,
            (device_id, user_id, message_id, transaction_id),
        ).lastrowid
        row = self.conn.execute(
            "SELECT estado, entregado_en, leido_en FROM dispositivos_notificaciones WHERE id = ?",
            (notification_id,),
        ).fetchone()
        self.assertEqual(tuple(row), ("pendiente", None, None))

        self.conn.execute(
            """
            UPDATE dispositivos_notificaciones
               SET estado = 'entregada', entregado_en = '2026-11-02T12:05:00Z'
             WHERE id = ?
            """,
            (notification_id,),
        )
        self.conn.execute(
            """
            UPDATE dispositivos_notificaciones
               SET estado = 'leida', leido_en = '2026-11-02T12:06:00Z'
             WHERE id = ?
            """,
            (notification_id,),
        )
        row = self.conn.execute(
            "SELECT estado, entregado_en, leido_en FROM dispositivos_notificaciones WHERE id = ?",
            (notification_id,),
        ).fetchone()
        self.assertEqual(row[0], "leida")
        self.assertIsNotNone(row[1])
        self.assertIsNotNone(row[2])

        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO dispositivos_notificaciones
                    (dispositivo_id, usuario_id, tipo, titulo, estado)
                VALUES (?, ?, 'movimiento_registrado', 'Invalida', 'leida')
                """,
                (device_id, user_id),
            )

    def test_user_delete_cascades(self):
        user_id = self.create_user()
        self.conn.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM cuentas WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0],
            0,
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) FROM estado_mascota WHERE usuario_id = ?", (user_id,)
            ).fetchone()[0],
            0,
        )

    def test_wellbeing_coverage(self):
        user_id = self.create_user()
        self.conn.execute(
            """
            UPDATE perfil_financiero
               SET estres_financiero = 5,
                   se_siente_seguro = 1,
                   dificultad_llevar_cuentas = 2,
                   tiene_deuda_tarjeta = 0,
                   tiene_fondo_emergencia = 1,
                   ingreso_trabajo_mensual = 0,
                   ahorro_mensual = 0
             WHERE usuario_id = ?
            """,
            (user_id,),
        )
        row = self.conn.execute(
            "SELECT puntaje, cobertura FROM v_bienestar_financiero WHERE usuario_id = ?",
            (user_id,),
        ).fetchone()
        self.assertIsNotNone(row[0])
        self.assertEqual(row[1], 90)


if __name__ == "__main__":
    unittest.main()
