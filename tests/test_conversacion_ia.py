"""Pruebas del interprete conversacional (Fase 7).

El LLM solo interpreta: aqui se comprueba que el prompt incluya el contexto,
que la respuesta se valide y que las reglas de respaldo reconozcan las frases
principales sin necesidad de un proveedor.
"""

import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import ai, nlp  # noqa: E402


class PromptConversacionalTests(unittest.TestCase):
    def test_incluye_contexto_y_catalogo(self):
        prompt = ai._armar_prompt_conversacion(
            "ahorré 50 mil para mi nuevo celular",
            {
                "fecha": "2026-11-05",
                "estado": "confirmando_movimiento",
                "borrador": {"nombre": "Audífonos"},
                "accion_pendiente": {"tipo": "confirmar_mensaje"},
                "metas": [{"nombre": "Mi nuevo celular"}],
                "cuentas": [{"nombre": "Nequi"}],
                "categorias": [{"nombre": "Alimentación", "tipo": "gasto"}],
            },
        )
        self.assertIn("Mi nuevo celular", prompt)
        self.assertIn("Nequi", prompt)
        self.assertIn("Alimentación", prompt)
        self.assertIn("2026-11-05", prompt)
        self.assertIn("registrar_movimiento", prompt)
        self.assertIn("confirmar", prompt)
        self.assertIn("JSON", prompt)


class InterpretarConversacionTests(unittest.TestCase):
    def test_respuesta_valida(self):
        crudo = {
            "intent": "crear_meta",
            "entidades": {"nombre": "Audífonos", "monto": 500000},
            "confianza": 0.9,
        }
        with mock.patch.object(ai, "proveedor_llm", return_value=ai.PROVEEDOR_LLM_OLLAMA):
            with mock.patch.object(ai, "_extraer_con_ollama", return_value=crudo):
                resultado = ai.interpretar_conversacion("quiero unos audífonos")
        self.assertEqual(resultado["intent"], "crear_meta")
        self.assertEqual(resultado["entidades"]["monto"], 500000)
        self.assertEqual(resultado["proveedor"], ai.PROVEEDOR_LLM_OLLAMA)

    def test_intencion_inventada_se_rechaza(self):
        crudo = {"intent": "borrar_todo", "entidades": {}, "confianza": 1}
        with mock.patch.object(ai, "proveedor_llm", return_value=ai.PROVEEDOR_LLM_OLLAMA):
            with mock.patch.object(ai, "_extraer_con_ollama", return_value=crudo):
                self.assertIsNone(ai.interpretar_conversacion("haz algo"))

    def test_confianza_se_limita_al_rango(self):
        crudo = {"intent": "ayuda", "entidades": None, "confianza": 9}
        with mock.patch.object(ai, "proveedor_llm", return_value=ai.PROVEEDOR_LLM_OLLAMA):
            with mock.patch.object(ai, "_extraer_con_ollama", return_value=crudo):
                resultado = ai.interpretar_conversacion("ayuda")
        self.assertEqual(resultado["entidades"], {})
        self.assertEqual(resultado["confianza"], 1.0)

    def test_sin_proveedor_devuelve_none(self):
        with mock.patch.object(ai, "proveedor_llm", return_value=None):
            self.assertIsNone(ai.interpretar_conversacion("hola"))


class ReglasConversacionalesTests(unittest.TestCase):
    def interpretar(self, texto):
        return nlp.detectar_intencion_conversacional(texto)

    def test_confirmaciones_naturales(self):
        for frase in ("sí", "ok", "correcto", "está bien", "confirmo"):
            self.assertEqual(self.interpretar(frase)["intent"], "confirmar", frase)

    def test_cancelaciones(self):
        for frase in ("no", "cancela", "olvídalo", "descarta"):
            self.assertEqual(self.interpretar(frase)["intent"], "cancelar", frase)

    def test_balance_por_periodo(self):
        hoy = self.interpretar("¿cómo me fue hoy?")
        self.assertEqual(hoy["intent"], "consultar_balance")
        self.assertEqual(hoy["entidades"]["periodo"], "hoy")

        semanal = self.interpretar("balance de esta semana")
        self.assertEqual(semanal["intent"], "consultar_balance")
        self.assertEqual(semanal["entidades"]["fecha_texto"], "balance de esta semana")
        self.assertEqual(
            nlp.resolver_rango(semanal["entidades"]["fecha_texto"])["alcance"],
            "semana",
        )

        mensual = self.interpretar("balance del mes")
        self.assertEqual(mensual["intent"], "consultar_balance")
        self.assertEqual(mensual["entidades"]["fecha_texto"], "balance del mes")
        self.assertEqual(
            nlp.resolver_rango(mensual["entidades"]["fecha_texto"])["alcance"], "mes"
        )

    def test_consulta_de_metas_y_plan(self):
        self.assertEqual(self.interpretar("¿cómo van mis metas?")["intent"], "consultar_metas")
        self.assertEqual(
            self.interpretar("¿cuánto debo ahorrar este mes?")["intent"], "consultar_plan"
        )

    def test_crear_meta_sin_monto(self):
        resultado = self.interpretar("quiero plantear una meta para comprarme unos audífonos")
        self.assertEqual(resultado["intent"], "crear_meta")
        self.assertEqual(resultado["entidades"]["nombre"], "audifonos")

    def test_movimiento_con_monto(self):
        resultado = self.interpretar("gasté 20 mil en almuerzo")
        self.assertEqual(resultado["intent"], "registrar_movimiento")
        self.assertEqual(resultado["entidades"]["monto"], 20000)

    def test_ahorro_con_monto(self):
        resultado = self.interpretar("ahorré 50 mil para mi nuevo celular")
        self.assertEqual(resultado["intent"], "registrar_movimiento")
        self.assertEqual(resultado["entidades"]["tipo"], "ahorro")


class PlazoYFrecuenciaTests(unittest.TestCase):
    def test_plazos_en_meses(self):
        resultado = nlp.parse_plazo("en cinco meses", date(2026, 11, 5))
        self.assertEqual(resultado["meses"], 5)
        self.assertEqual(resultado["fecha_limite"], "2027-04-05")

    def test_plazos_en_semanas(self):
        resultado = nlp.parse_plazo("en 3 semanas", date(2026, 11, 5))
        self.assertEqual(resultado["dias"], 21)
        self.assertEqual(resultado["fecha_limite"], "2026-11-26")

    def test_plazo_en_anios(self):
        resultado = nlp.parse_plazo("en un año", date(2026, 11, 5))
        self.assertEqual(resultado["meses"], 12)
        self.assertEqual(resultado["fecha_limite"], "2027-11-05")

    def test_frecuencias(self):
        self.assertEqual(nlp.parse_frecuencia("mensual"), "mensual")
        self.assertEqual(nlp.parse_frecuencia("cada semana"), "semanal")
        self.assertEqual(nlp.parse_frecuencia("cada quincena"), "quincenal")
        self.assertEqual(nlp.parse_frecuencia("todos los días"), "diaria")
        self.assertIsNone(nlp.parse_frecuencia("cuando pueda"))

    def test_prioridad(self):
        self.assertEqual(nlp.detect_priority("prioridad alta"), 1)
        self.assertEqual(nlp.detect_priority("prioridad 4"), 4)
        self.assertEqual(nlp.detect_priority("baja"), 5)
        self.assertEqual(nlp.detect_priority("normal"), 3)
        self.assertIsNone(nlp.detect_priority("sin preferencia"))


if __name__ == "__main__":
    unittest.main()
