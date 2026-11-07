import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulator import pantallas  # noqa: E402

HOME = {
    "mascota": {"animo": "FELIZ", "salud": 92},
    "hoy": {
        "ingresos": 800000,
        "gastos": 20000,
        "ahorro": 50000,
        "balance_neto": 830000,
        "cupo_restante": 10000,
        "presupuesto_diario": 30000,
    },
    "puntos": 3,
}


class PantallasTests(unittest.TestCase):
    def test_todas_las_pantallas_caben_en_el_marco(self):
        pantallas_creadas = [
            pantallas.d01_arranque(),
            pantallas.d02_sin_vincular(),
            pantallas.d03_reposo(HOME),
            pantallas.d04_grabando(3),
            pantallas.d05_procesando(),
            pantallas.d06_confirmar(
                [{"tipo": "gasto", "monto": 20000, "categoria": "Alimentación", "cuenta": "Nequi"}],
                "gasté veinte mil por nequi",
            ),
            pantallas.d07_resultado(1, HOME),
            pantallas.d08_consulta(HOME),
            pantallas.d09_cierre(
                {
                    "total_ingresos": 800000,
                    "total_gastos": 20000,
                    "total_ahorrado": 50000,
                    "balance_neto": 830000,
                    "salud_fin": 92,
                    "animo": "FELIZ",
                }
            ),
            pantallas.d10_sin_conexion(),
            pantallas.d11_no_entendio(),
            pantallas.d12_bloqueado(),
            pantallas.d13_aviso("Aviso", "Texto del aviso"),
            pantallas.d14_plan_ahorro(
                {
                    "capacidad_mes_actual": 250000,
                    "resumen": {
                        "metas_totales": 2,
                        "cumplimiento_ponderado": 0.5,
                    },
                    "metas": [
                        {
                            "meta_id": 1,
                            "nombre": "Fondo de emergencia",
                            "asignacion_mes_actual": 30000,
                            "cumplimiento": 0.4,
                        }
                    ],
                    "diagnostico": {"mensaje": "La capacidad alcanza para el 50 %."},
                }
            ),
        ]
        for pantalla in pantallas_creadas:
            lineas = pantalla.splitlines()
            self.assertTrue(lineas[0].startswith("+"), pantalla)
            self.assertTrue(lineas[-1].startswith("+"), pantalla)
            anchos = {len(linea) for linea in lineas}
            self.assertEqual(len(anchos), 1, f"anchos desiguales: {anchos}")

    def test_la_consulta_muestra_el_balance_completo(self):
        texto = pantallas.d08_consulta(HOME)
        self.assertIn("800.000", texto)  # ingresos
        self.assertIn("20.000", texto)  # gastos
        self.assertIn("50.000", texto)  # ahorro
        self.assertIn("830.000", texto)  # balance
        self.assertIn("10.000", texto)  # cupo restante
        self.assertIn("FELIZ", texto)
        self.assertIn("92", texto)

    def test_el_reposo_muestra_ingresos_y_gastos(self):
        texto = pantallas.d03_reposo(HOME)
        self.assertIn("800.000", texto)
        self.assertIn("20.000", texto)
        self.assertIn("Puntos", texto)
        self.assertIn("Mant", texto)

    def test_confirmar_muestra_tipo_monto_categoria_y_cuenta(self):
        texto = pantallas.d06_confirmar(
            [{"tipo": "gasto", "monto": 20000, "categoria": "Alimentación", "cuenta": "Nequi"}],
            "gasté veinte mil por nequi",
        )
        self.assertIn("GASTO", texto)
        self.assertIn("20.000", texto)
        self.assertIn("Alimentación", texto)
        self.assertIn("Nequi", texto)

    def test_dinero_negativo(self):
        home = dict(HOME)
        hoy = dict(HOME["hoy"])
        hoy["cupo_restante"] = -4000
        home["hoy"] = hoy
        texto = pantallas.d08_consulta(home)
        self.assertIn("-$4.000", texto)
        self.assertNotIn("$-4.000", texto)

    def test_el_mensaje_de_nancy_cambia_con_el_animo(self):
        texto_feliz = pantallas.d08_consulta(HOME)
        home = dict(HOME)
        home["mascota"] = {"animo": "CRITICO", "salud": 30}
        texto_critico = pantallas.d08_consulta(home)
        self.assertNotEqual(
            [l for l in texto_feliz.splitlines() if "Vas muy bien" in l],
            [l for l in texto_critico.splitlines() if "Vas muy bien" in l],
        )
        self.assertIn("CRITICO", texto_critico)

    def test_el_menu_ofrece_las_acciones_del_dispositivo(self):
        menu = pantallas.menu()
        for opcion in ("[H]", "[E]", "[C]", "[P]", "[N]", "[S]"):
            self.assertIn(opcion, menu)

    def test_el_menu_es_voz_primero_y_ofrece_texto_y_microfono(self):
        menu = pantallas.menu()
        self.assertIn("Habla con Nancy", menu)
        self.assertIn("[T] Escribir", menu)
        self.assertIn("[A] Probar micrófono", menu)
        self.assertIn("[V] Voz", menu)
        self.assertIn("Quiero crear una meta", menu)

    def test_la_pantalla_conversacional_muestra_a_nancy(self):
        texto = pantallas.d15_conversacion(
            {
                "mensaje_nancy": "Entendí un GASTO de $20.000 en Alimentación. ¿Está correcto?",
                "estado_conversacion": "confirmando_movimiento",
                "requiere_confirmacion": True,
                "datos": {"transaccion": {"tipo": "gasto", "monto": 20000}},
            }
        )
        self.assertIn("NANCY", texto)
        self.assertIn("20.000", texto)
        self.assertIn("Di sí", texto)
        self.assertIn("[H] Hablar", texto)
        self.assertNotIn("Estado:", texto)
        self.assertNotIn("confirmando_movimiento", texto)
        lineas = texto.splitlines()
        self.assertEqual(len({len(linea) for linea in lineas}), 1)

    def test_la_voz_por_defecto_cubre_las_consultas(self):
        from simulator.main import DEFAULT_CONFIG

        self.assertEqual(DEFAULT_CONFIG["voice_scope"], "resumen")

    def test_la_pantalla_de_consulta_muestra_rango_y_movimientos(self):
        texto = pantallas.d15_conversacion(
            {
                "mensaje_nancy": "Ayer registraste 2 movimientos.",
                "tipo_respuesta": "consulta",
                "estado_conversacion": "inactiva",
                "datos": {
                    "rango": {"etiqueta": "ayer"},
                    "resumen": {
                        "total_ingresos": 0,
                        "total_gastos": 20000,
                        "total_ahorrado": 5000,
                        "balance_neto": -20000,
                    },
                    "movimientos": [
                        {
                            "tipo": "gasto",
                            "monto": 20000,
                            "fecha_local": "2026-11-05",
                            "categoria": "Alimentación",
                        }
                    ],
                },
            }
        )
        self.assertIn("20.000", texto)
        self.assertIn("05/11", texto)
        self.assertIn("Alimentación", texto)
        self.assertIn("Rango: ayer", texto)
        self.assertNotIn("Estado:", texto)

    def test_pantalla_de_error_explica_el_motivo(self):
        texto = pantallas.d16_error(
            "STT_SIN_TEXTO", "No se pudo transcribir el audio", "pico 1"
        )
        self.assertIn("STT_SIN_TEXTO", texto)
        self.assertIn("pico 1", texto)
        self.assertIn("[T] Escribir", texto)

    def test_pantalla_de_microfono_avisa_silencio(self):
        texto = pantallas.d17_microfono("Realtek", 1, 0.48, False)
        self.assertIn("Realtek", texto)
        self.assertIn("Casi no hay señal", texto)


class AudioSimuladorTests(unittest.TestCase):
    def test_estadisticas_detectan_silencio(self):
        from simulator import main as simulador_main

        stats = simulador_main._estadisticas_audio([0, 0, 0, 0])
        self.assertEqual(stats["pico"], 0)
        self.assertEqual(stats["rms"], 0.0)
        self.assertEqual(stats["muestras"], 4)

    def test_el_plan_de_ahorro_muestra_capacidad_y_metas(self):
        texto = pantallas.d14_plan_ahorro(
            {
                "capacidad_mes_actual": 250000,
                "resumen": {"metas_totales": 1, "cumplimiento_ponderado": 0.4},
                "metas": [
                    {
                        "meta_id": 1,
                        "nombre": "Fondo",
                        "asignacion_mes_actual": 30000,
                        "cumplimiento": 0.4,
                    }
                ],
                "diagnostico": {"mensaje": "Capacidad limitada."},
            }
        )
        self.assertIn("250.000", texto)
        self.assertIn("Fondo", texto)
        self.assertIn("30.000", texto)
        self.assertIn("40", texto)


if __name__ == "__main__":
    unittest.main()
