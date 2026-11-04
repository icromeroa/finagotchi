"""Pruebas de integridad del dataset demo generado por ``tools``."""

import csv
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "tools"))

import generar_dataset_bd as generador  # noqa: E402
from werkzeug.security import check_password_hash  # noqa: E402


class DatasetBdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp.name) / "dataset.db"
        cls.hoy = date.today()
        cls.resumen, _, _ = generador.generar_dataset(
            cls.db_path,
            usuarios=25,
            dispositivos=18,
            transacciones=500,
            dias=120,
            semilla=20261104,
            respaldar=False,
            exportar=False,
            hoy=cls.hoy,
        )
        cls.conn = sqlite3.connect(cls.db_path)
        cls.conn.row_factory = sqlite3.Row
        cls.conn.execute("PRAGMA foreign_keys = ON")

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls.temp.cleanup()

    def scalar(self, sql, params=()):
        return self.conn.execute(sql, params).fetchone()[0]

    # ------------------------------------------------------------------
    # Estructura y volumen
    # ------------------------------------------------------------------
    def test_conteos_principales(self):
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM usuarios"), 25)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM dispositivos"), 18)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM transacciones"), 500)
        self.assertEqual(self.resumen["usuarios_solo_app"], 7)
        self.assertEqual(self.resumen["usuarios_con_dispositivo"], 18)

    def test_nunca_hay_mas_dispositivos_que_usuarios(self):
        usuarios = self.scalar("SELECT COUNT(*) FROM usuarios")
        dispositivos = self.scalar("SELECT COUNT(*) FROM dispositivos")
        self.assertLessEqual(dispositivos, usuarios)
        repetidos = self.conn.execute(
            """
            SELECT usuario_id, COUNT(*) FROM dispositivos
             GROUP BY usuario_id HAVING COUNT(*) > 1
            """
        ).fetchall()
        self.assertEqual(repetidos, [])
        self.assertEqual(
            self.scalar("SELECT COUNT(*) FROM dispositivos WHERE usuario_id IS NULL"),
            0,
        )

    def test_integridad_referencial(self):
        self.assertEqual(self.conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(
            self.conn.execute("PRAGMA integrity_check").fetchone()[0], "ok"
        )

    def test_todas_las_vistas_responden(self):
        vistas = [
            fila[0]
            for fila in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name"
            )
        ]
        self.assertEqual(len(vistas), 15)
        for vista in vistas:
            total = self.scalar(f'SELECT COUNT(*) FROM "{vista}"')
            self.assertGreaterEqual(total, 0, vista)
            self.conn.execute(f'SELECT * FROM "{vista}" LIMIT 1').fetchone()
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM v_puntos_usuario"), 25)

    def test_semilla_por_usuario(self):
        for tabla in (
            "perfil_financiero",
            "preferencias_notificacion",
            "progreso_etapa",
            "estado_mascota",
            "presupuesto_diario_historial",
        ):
            self.assertEqual(
                self.scalar(f"SELECT COUNT(DISTINCT usuario_id) FROM {tabla}"),
                25,
                tabla,
            )
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM perfil_secciones"), 150)
        for usuario_id in range(1, 26):
            self.assertGreaterEqual(
                self.scalar(
                    "SELECT COUNT(*) FROM categorias WHERE usuario_id = ?",
                    (usuario_id,),
                ),
                16,
            )
            self.assertGreaterEqual(
                self.scalar(
                    "SELECT COUNT(*) FROM cuentas WHERE usuario_id = ?",
                    (usuario_id,),
                ),
                5,
            )

    # ------------------------------------------------------------------
    # Coherencia financiera
    # ------------------------------------------------------------------
    def test_puntos_por_transaccion_confirmada(self):
        confirmadas = self.scalar(
            "SELECT COUNT(*) FROM transacciones WHERE estado = 'confirmado' AND is_deleted = 0"
        )
        con_puntos = self.scalar(
            """
            SELECT COUNT(DISTINCT t.id)
              FROM transacciones t
              JOIN puntos_log p
                ON p.usuario_id = t.usuario_id
               AND p.transaccion_id = t.id
               AND p.motivo = 'registro_valido'
             WHERE t.estado = 'confirmado' AND t.is_deleted = 0
            """
        )
        self.assertEqual(confirmadas, con_puntos)
        duplicados = self.conn.execute(
            """
            SELECT usuario_id, transaccion_id, COUNT(*)
              FROM puntos_log
             WHERE motivo = 'registro_valido'
             GROUP BY usuario_id, transaccion_id
            HAVING COUNT(*) > 1
            """
        ).fetchall()
        self.assertEqual(duplicados, [])

    def test_balances_coinciden_con_las_transacciones(self):
        fila = self.conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN tipo = 'ahorro' THEN monto ELSE 0 END), 0),
                COUNT(*)
              FROM transacciones
             WHERE estado = 'confirmado' AND is_deleted = 0
            """
        ).fetchone()
        vista = self.conn.execute(
            """
            SELECT COALESCE(SUM(total_ingresos), 0),
                   COALESCE(SUM(total_gastos), 0),
                   COALESCE(SUM(total_ahorrado), 0),
                   COALESCE(SUM(num_registros), 0)
              FROM v_balance_diario
            """
        ).fetchone()
        self.assertEqual(tuple(fila), tuple(vista))

        mensual = self.conn.execute(
            """
            SELECT COALESCE(SUM(total_ingresos), 0),
                   COALESCE(SUM(total_gastos), 0),
                   COALESCE(SUM(total_ahorrado), 0),
                   COALESCE(SUM(num_registros), 0)
              FROM v_balance_mensual
            """
        ).fetchone()
        self.assertEqual(tuple(fila), tuple(mensual))

    def test_reglas_de_ahorro_y_categorias(self):
        malos = self.conn.execute(
            """
            SELECT COUNT(*) FROM transacciones
             WHERE (tipo = 'ahorro' AND (categoria_id IS NOT NULL OR meta_id IS NULL))
                OR (tipo <> 'ahorro' AND (categoria_id IS NULL OR meta_id IS NOT NULL))
            """
        ).fetchone()[0]
        self.assertEqual(malos, 0)

    def test_cuentas_y_metas_pertenecen_al_usuario(self):
        for tabla, columna in (
            ("transacciones", "cuenta_id"),
            ("transacciones", "categoria_id"),
            ("transacciones", "meta_id"),
            ("gastos_fijos", "categoria_id"),
            ("gastos_fijos", "cuenta_id"),
            ("presupuesto_categoria", "categoria_id"),
        ):
            if columna == "categoria_id" and tabla == "transacciones":
                sql = """
                    SELECT COUNT(*) FROM transacciones t
                     WHERE t.categoria_id IS NOT NULL
                       AND NOT EXISTS (
                           SELECT 1 FROM categorias c
                            WHERE c.id = t.categoria_id AND c.usuario_id = t.usuario_id
                       )
                """
            elif columna == "meta_id":
                sql = """
                    SELECT COUNT(*) FROM transacciones t
                     WHERE t.meta_id IS NOT NULL
                       AND NOT EXISTS (
                           SELECT 1 FROM metas m
                            WHERE m.id = t.meta_id AND m.usuario_id = t.usuario_id
                       )
                """
            else:
                sql = f"""
                    SELECT COUNT(*) FROM {tabla} x
                     WHERE x.{columna} IS NOT NULL
                       AND NOT EXISTS (
                           SELECT 1 FROM cuentas c
                            WHERE c.id = x.{columna} AND c.usuario_id = x.usuario_id
                       )
                """ if columna == "cuenta_id" else f"""
                    SELECT COUNT(*) FROM {tabla} x
                     WHERE x.{columna} IS NOT NULL
                       AND NOT EXISTS (
                           SELECT 1 FROM categorias c
                            WHERE c.id = x.{columna} AND c.usuario_id = x.usuario_id
                       )
                """
            self.assertEqual(self.scalar(sql), 0, f"{tabla}.{columna}")

    def test_cierres_y_salud(self):
        self.assertGreater(self.scalar("SELECT COUNT(*) FROM cierres_dia"), 0)
        descuadres = self.conn.execute(
            """
            SELECT COUNT(*) FROM cierres_dia
             WHERE salud_inicio IS NULL OR salud_fin IS NULL
                OR salud_fin < 0 OR salud_fin > 100
            """
        ).fetchone()[0]
        self.assertEqual(descuadres, 0)
        self.assertEqual(
            self.scalar("SELECT COUNT(*) FROM cierres_dia"),
            self.scalar("SELECT COUNT(*) FROM salud_log WHERE motivo = 'cierre_dia'"),
        )
        for fila in self.conn.execute("SELECT salud FROM estado_mascota"):
            self.assertGreaterEqual(fila[0], 0)
            self.assertLessEqual(fila[0], 100)

    # ------------------------------------------------------------------
    # Casos limite y seguridad
    # ------------------------------------------------------------------
    def test_casos_limite(self):
        self.assertGreater(
            self.scalar("SELECT COUNT(*) FROM transacciones WHERE estado = 'pendiente'"), 0
        )
        self.assertGreater(
            self.scalar("SELECT COUNT(*) FROM transacciones WHERE is_deleted = 1"), 0
        )
        self.assertGreater(
            self.scalar("SELECT COUNT(*) FROM transacciones_versiones"), 0
        )
        self.assertGreater(
            self.scalar("SELECT COUNT(*) FROM metas WHERE estado = 'completada'"), 0
        )
        self.assertGreater(
            self.scalar("SELECT COUNT(*) FROM alertas_log WHERE is_deleted = 1"), 0
        )

        self.assertEqual(
            self.scalar(
                "SELECT COUNT(*) FROM solicitudes_eliminacion_cuenta WHERE estado = 'pendiente'"
            ),
            2,
        )
        self.assertEqual(
            self.scalar(
                "SELECT COUNT(*) FROM solicitudes_eliminacion_cuenta WHERE estado = 'cancelada'"
            ),
            1,
        )
        self.assertEqual(
            self.scalar(
                "SELECT COUNT(*) FROM usuarios WHERE estado = 'pendiente_eliminacion'"
            ),
            2,
        )
        self.assertGreater(
            self.scalar("SELECT COUNT(*) FROM tokens_recuperacion WHERE usado_en IS NOT NULL"),
            0,
        )
        self.assertGreater(
            self.scalar("SELECT COUNT(*) FROM sesiones_refresco WHERE revocado_en IS NOT NULL"),
            0,
        )
        self.assertGreater(self.scalar("SELECT COUNT(*) FROM retos_respuestas"), 0)

    def test_contrasenas_demo(self):
        casos = [
            ("simulador@finagotchi.local", "simulador123"),
            ("demo01@finagotchi.local", "Demo1234"),
            ("demo24@finagotchi.local", "Demo1234"),
        ]
        for correo, password in casos:
            fila = self.conn.execute(
                "SELECT password_hash FROM usuarios WHERE correo = ?", (correo,)
            ).fetchone()
            self.assertIsNotNone(fila, correo)
            self.assertTrue(check_password_hash(fila[0], password), correo)
        self.assertEqual(
            self.scalar("SELECT COUNT(*) FROM usuarios WHERE correo_verificado = 1"), 25
        )

    def test_no_guarda_audio_en_la_base(self):
        columnas = []
        for (tabla,) in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ):
            for columna in self.conn.execute(f"PRAGMA table_info('{tabla}')"):
                columnas.append((tabla, columna[1], columna[2]))
        sospechosas = [
            item for item in columnas
            if item[1].lower() in ("audio", "audio_blob", "wav", "archivo")
            or item[2].upper() == "BLOB"
        ]
        self.assertEqual(sospechosas, [])
        fila = self.conn.execute(
            "SELECT entrada_json FROM interacciones_ia LIMIT 1"
        ).fetchone()
        self.assertNotIn("base64", (fila[0] or "").lower())

    # ------------------------------------------------------------------
    # Exportacion
    # ------------------------------------------------------------------
    def test_exportacion_csv_y_manifest(self):
        salida = Path(self.temp.name) / "exportado"
        manifest = generador.exportar_csv(
            self.db_path,
            self.resumen,
            semilla=20261104,
            salida=salida,
            hoy=self.hoy,
        )
        tablas = [
            fila[0]
            for fila in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        self.assertEqual(manifest["total_archivos"], len(tablas))
        self.assertEqual(len(list((salida / "csv").glob("*.csv"))), len(tablas))
        self.assertTrue((salida / "manifest.json").exists())
        self.assertTrue((salida / "README.md").exists())

        for item in manifest["archivos"]:
            ruta = salida / item["archivo"]
            self.assertTrue(ruta.exists(), item["archivo"])
            contenido = ruta.read_bytes()
            self.assertEqual(
                hashlib.sha256(contenido).hexdigest(), item["sha256"], item["archivo"]
            )
            with ruta.open(encoding="utf-8", newline="") as archivo:
                lector = csv.reader(archivo)
                encabezado = next(lector)
                filas = sum(1 for _ in lector)
            self.assertEqual(filas, item["filas"], item["archivo"])
            self.assertFalse(contenido.startswith(b"\xef\xbb\xbf"))
            columnas = [
                fila[1]
                for fila in self.conn.execute(f"PRAGMA table_xinfo('{item['tabla']}')")
            ]
            self.assertEqual(encabezado, columnas, item["archivo"])

        guardado = json.loads((salida / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(guardado["semilla"], 20261104)
        self.assertEqual(guardado["resumen"]["usuarios"], 25)


if __name__ == "__main__":
    unittest.main()
