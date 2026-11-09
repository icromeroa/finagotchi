"""Pruebas deterministas del resolutor de fechas de FinaGotchi.

El LLM solo copia la expresión temporal. Estas pruebas fijan la traducción a
fechas reales para que «esta semana» sea siempre lunes a hoy y no dependa del
modelo ni del reloj de la máquina.
"""

import unittest
from datetime import date

from backend import nlp

# Viernes 6 de noviembre de 2026: una semana ya empezada, ideal para probar
# que «esta semana» arranca el lunes y termina hoy.
HOY = date(2026, 11, 6)


class ResolverRangoTests(unittest.TestCase):
    def resolver(self, texto):
        return nlp.resolver_rango(texto, hoy=HOY)

    def test_hoy_ayer_y_anteayer(self):
        hoy = self.resolver("¿cómo me fue hoy?")
        self.assertEqual((hoy["desde"], hoy["hasta"]), ("2026-11-06", "2026-11-06"))
        self.assertEqual(hoy["etiqueta"], "hoy")
        self.assertEqual(hoy["alcance"], "dia")

        ayer = self.resolver("mis gastos de ayer")
        self.assertEqual((ayer["desde"], ayer["hasta"]), ("2026-11-05", "2026-11-05"))
        self.assertEqual(ayer["etiqueta"], "ayer")

        anteayer = self.resolver("lo que gasté anteayer")
        self.assertEqual(
            (anteayer["desde"], anteayer["hasta"]), ("2026-11-04", "2026-11-04")
        )
        self.assertEqual(anteayer["etiqueta"], "anteayer")

    def test_esta_semana_es_lunes_a_hoy(self):
        rango = self.resolver("balance de esta semana")
        self.assertEqual((rango["desde"], rango["hasta"]), ("2026-11-02", "2026-11-06"))
        self.assertEqual(rango["alcance"], "semana")
        self.assertIn("lunes a hoy", rango["etiqueta"])

    def test_la_semana_pasada_es_la_semana_anterior_completa(self):
        rango = self.resolver("la semana pasada")
        self.assertEqual((rango["desde"], rango["hasta"]), ("2026-10-26", "2026-11-01"))
        self.assertEqual(rango["alcance"], "semana")

    def test_este_mes_y_el_mes_pasado(self):
        actual = self.resolver("cómo voy este mes")
        self.assertEqual((actual["desde"], actual["hasta"]), ("2026-11-01", "2026-11-06"))
        self.assertEqual(actual["alcance"], "mes")

        anterior = self.resolver("balance del mes pasado")
        self.assertEqual(
            (anterior["desde"], anterior["hasta"]), ("2026-10-01", "2026-10-31")
        )
        self.assertEqual(anterior["alcance"], "mes")

    def test_dia_suelto_con_mes_y_anio(self):
        rango = self.resolver("gasté 20 mil en comida el 3 de mayo")
        self.assertEqual((rango["desde"], rango["hasta"]), ("2026-05-03", "2026-05-03"))
        self.assertEqual(rango["etiqueta"], "3 de mayo de 2026")
        self.assertEqual(rango["alcance"], "dia")

        con_anio = self.resolver("movimientos del 31 de diciembre de 2027")
        self.assertEqual(
            (con_anio["desde"], con_anio["hasta"]), ("2027-12-31", "2027-12-31")
        )

    def test_formato_numerico(self):
        rango = self.resolver("movimientos del 05/11")
        self.assertEqual((rango["desde"], rango["hasta"]), ("2026-11-05", "2026-11-05"))
        con_anio = self.resolver("movimientos del 05/11/2025")
        self.assertEqual(
            (con_anio["desde"], con_anio["hasta"]), ("2025-11-05", "2025-11-05")
        )
        iso = self.resolver("movimientos de 2026-11-04")
        self.assertEqual((iso["desde"], iso["hasta"]), ("2026-11-04", "2026-11-04"))

    def test_rango_del_al(self):
        rango = self.resolver("gastos del 3 al 5 de mayo")
        self.assertEqual((rango["desde"], rango["hasta"]), ("2026-05-03", "2026-05-05"))
        self.assertEqual(rango["alcance"], "rango")
        self.assertEqual(rango["etiqueta"], "del 3 al 5 de mayo")

    def test_rango_que_cruza_de_mes(self):
        rango = self.resolver("movimientos del 28 de febrero al 2 de marzo")
        self.assertEqual((rango["desde"], rango["hasta"]), ("2026-02-28", "2026-03-02"))
        self.assertEqual(rango["alcance"], "rango")

    def test_sin_expresion_cae_en_hoy_sin_marcarla(self):
        rango = self.resolver("mis últimos movimientos")
        self.assertEqual((rango["desde"], rango["hasta"]), ("2026-11-06", "2026-11-06"))
        self.assertEqual(rango["expresion"], "")
        self.assertEqual(rango["alcance"], "dia")

    def test_acepta_fecha_iso_como_base(self):
        rango = nlp.resolver_rango("ayer", hoy="2026-11-06")
        self.assertEqual((rango["desde"], rango["hasta"]), ("2026-11-05", "2026-11-05"))

    def test_la_fecha_negada_no_gana_a_la_afirmada(self):
        rango = self.resolver("no es de ayer, es de hoy")
        self.assertEqual((rango["desde"], rango["hasta"]), ("2026-11-06", "2026-11-06"))
        self.assertEqual(rango["etiqueta"], "hoy")

        negada = self.resolver("no fue ayer")
        self.assertEqual(negada["expresion"], "")


if __name__ == "__main__":
    unittest.main()
