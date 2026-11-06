import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend import ai, nlp  # noqa: E402


class Cursor:
    """Cursor de SQLite minimo para las pruebas."""

    def __init__(self, filas):
        self.filas = list(filas)

    def fetchall(self):
        return list(self.filas)

    def fetchone(self):
        return self.filas[0] if self.filas else None

    def __iter__(self):
        return iter(self.filas)


class JsonDeTextoTests(unittest.TestCase):
    def test_json_limpio(self):
        self.assertEqual(ai._json_de_texto('{"tipo": "gasto"}'), {"tipo": "gasto"})

    def test_json_envuelto_en_codigo(self):
        texto = '```json\n{"tipo": "gasto", "monto": 100}\n```'
        self.assertEqual(ai._json_de_texto(texto)["monto"], 100)

    def test_json_con_texto_alrededor(self):
        texto = 'Aqui esta: {"tipo": "gasto"} espero que sirva'
        self.assertEqual(ai._json_de_texto(texto)["tipo"], "gasto")

    def test_texto_invalido(self):
        self.assertIsNone(ai._json_de_texto("no soy json"))
        self.assertIsNone(ai._json_de_texto(""))


class PromptDeExtraccionTests(unittest.TestCase):
    def test_el_prompt_incluye_el_catalogo(self):
        prompt = ai._armar_prompt_extraccion(
            "gasté 20000 por nequi",
            [{"nombre": "Alimentación", "tipo": "gasto"}],
            [{"nombre": "Nequi"}],
        )
        self.assertIn("Alimentación", prompt)
        self.assertIn("Nequi", prompt)
        self.assertIn("gasté 20000 por nequi", prompt)
        self.assertIn("JSON", prompt)


class CoincidenciaEnCatalogoTests(unittest.TestCase):
    CATALOGO = [
        {"id": 1, "nombre": "Nequi"},
        {"id": 2, "nombre": "Daviplata"},
        {"id": 3, "nombre": "Alimentación"},
    ]

    def test_coincidencia_exacta(self):
        self.assertEqual(
            nlp.coincide_en_catalogo("nequi", self.CATALOGO)["id"], 1
        )

    def test_coincidencia_sin_tildes_ni_mayusculas(self):
        self.assertEqual(
            nlp.coincide_en_catalogo("ALIMENTACIÓN", self.CATALOGO)["id"], 3
        )

    def test_coincidencia_aproximada_de_un_caracter(self):
        self.assertEqual(nlp.coincide_en_catalogo("Neqi", self.CATALOGO)["id"], 1)
        self.assertEqual(
            nlp.coincide_en_catalogo("Davi Plata", self.CATALOGO)["id"], 2
        )

    def test_sin_coincidencia(self):
        self.assertIsNone(nlp.coincide_en_catalogo("bancolombia", self.CATALOGO))
        self.assertIsNone(nlp.coincide_en_catalogo(None, self.CATALOGO))
        self.assertIsNone(nlp.coincide_en_catalogo("", self.CATALOGO))


class InterpretarConIaTests(unittest.TestCase):
    def setUp(self):
        self.conn = mock.MagicMock()
        self.categorias = [
            {"id": 1, "nombre": "Alimentación", "tipo": "gasto"},
            {"id": 2, "nombre": "Transporte", "tipo": "gasto"},
            {"id": 3, "nombre": "Trabajo", "tipo": "ingreso"},
        ]
        self.cuentas = [
            {"id": 1, "nombre": "Efectivo"},
            {"id": 2, "nombre": "Nequi"},
        ]

        def consultar(consulta, *args):
            if "FROM categorias" in consulta and "nombre = ?" in consulta:
                # Consulta de la categoria de ultimo recurso.
                return Cursor([{"id": 9, "nombre": "Otros", "tipo": "gasto"}])
            if "FROM categorias" in consulta:
                return Cursor([dict(c) for c in self.categorias])
            if "FROM cuentas" in consulta and "es_por_defecto" not in consulta:
                return Cursor([dict(c) for c in self.cuentas])
            if "es_por_defecto" in consulta:
                return Cursor([{"id": 1, "nombre": "Efectivo"}])
            return Cursor([])

        self.conn.execute.side_effect = consultar

    def _interpretar(self, respuesta):
        with mock.patch.object(ai, "extraer_estructura", return_value=respuesta):
            return nlp.interpretar_con_ia(self.conn, 7, "gasté 20000 por nequi")

    def test_ia_asigna_categoria_y_cuenta(self):
        resultado = self._interpretar(
            {
                "tipo": "gasto",
                "monto": 20000,
                "categoria": "Alimentación",
                "cuenta": "Nequi",
                "concepto": "almuerzo",
                "proveedor": "ollama",
            }
        )
        self.assertEqual(resultado["origen"], "ia")
        transaccion = resultado["transacciones"][0]
        self.assertEqual(transaccion["monto"], 20000)
        self.assertEqual(transaccion["categoria"], "Alimentación")
        self.assertEqual(transaccion["cuenta"], "Nequi")
        self.assertEqual(transaccion["concepto"], "almuerzo")

    def test_ia_rechaza_categoria_inventada_y_usa_la_de_ultimo_recurso(self):
        resultado = self._interpretar(
            {
                "tipo": "gasto",
                "monto": 20000,
                "categoria": "Bicicletas espaciales",
                "cuenta": "Nequi",
            }
        )
        # Nunca se guarda la categoria inventada: entra la de ultimo recurso.
        self.assertNotEqual(resultado["transacciones"][0]["categoria"], "Bicicletas espaciales")
        self.assertEqual(resultado["transacciones"][0]["categoria"], "Otros")

    def test_ia_rechaza_cuenta_inventada_y_usa_la_por_defecto(self):
        resultado = self._interpretar(
            {
                "tipo": "gasto",
                "monto": 20000,
                "categoria": "Alimentación",
                "cuenta": "Cuenta secreta",
            }
        )
        self.assertEqual(resultado["transacciones"][0]["cuenta"], "Efectivo")

    def test_ia_con_categoria_de_otro_tipo_se_descarta(self):
        resultado = self._interpretar(
            {
                "tipo": "gasto",
                "monto": 20000,
                "categoria": "Trabajo",
                "cuenta": "Nequi",
            }
        )
        self.assertNotEqual(resultado["transacciones"][0]["categoria"], "Trabajo")
        self.assertEqual(resultado["transacciones"][0]["categoria"], "Otros")

    def test_ia_sin_monto_usa_el_monto_de_las_reglas(self):
        resultado = self._interpretar(
            {"tipo": "gasto", "monto": None, "categoria": "Alimentación", "cuenta": "Nequi"}
        )
        self.assertEqual(resultado["transacciones"][0]["monto"], 20000)

    def test_ahorro_no_lleva_categoria(self):
        resultado = self._interpretar(
            {
                "tipo": "ahorro",
                "monto": 30000,
                "categoria": "Alimentación",
                "cuenta": "Nequi",
            }
        )
        self.assertIsNone(resultado["transacciones"][0]["categoria_id"])
        self.assertEqual(resultado["transacciones"][0]["tipo"], "ahorro")

    def test_todo_movimiento_distinto_de_ahorro_lleva_categoria(self):
        """El esquema exige categoria: el camino de IA no puede dejarla nula."""
        for tipo in ("gasto", "ingreso"):
            resultado = self._interpretar(
                {
                    "tipo": tipo,
                    "monto": 10000,
                    "categoria": None,
                    "cuenta": "Nequi",
                }
            )
            self.assertIsNotNone(
                resultado["transacciones"][0]["categoria_id"],
                f"Un movimiento de tipo {tipo} no puede quedar sin categoria",
            )

    def test_sin_llm_devuelve_none(self):
        with mock.patch.object(ai, "extraer_estructura", return_value=None):
            self.assertIsNone(nlp.interpretar_con_ia(self.conn, 7, "gasté 20000"))

    def test_error_del_llm_no_rompe_nada(self):
        with mock.patch.object(
            ai, "extraer_estructura", side_effect=ai.ErrorSTT("se cayo")
        ):
            self.assertIsNone(nlp.interpretar_con_ia(self.conn, 7, "gasté 20000"))

    def test_interpret_usa_la_ia_cuando_esta_disponible(self):
        propuesta = {
            "intent": "registrar",
            "texto": "gasté 20000 por nequi",
            "origen": "ia",
            "transacciones": [{"tipo": "gasto", "monto": 20000}],
        }
        with mock.patch.object(nlp, "interpretar_con_ia", return_value=propuesta):
            resultado = nlp.interpret(self.conn, 7, "gasté 20000 por nequi")
        self.assertEqual(resultado["origen"], "ia")

    def test_interpret_cae_a_las_reglas_si_la_ia_no_sirve(self):
        with mock.patch.object(nlp, "interpretar_con_ia", return_value=None):
            with mock.patch.object(nlp, "detect_category", return_value={"id": 1, "nombre": "Alimentación"}):
                with mock.patch.object(nlp, "detect_account", return_value={"id": 1, "nombre": "Efectivo"}):
                    resultado = nlp.interpret(self.conn, 7, "gasté 20000 en almuerzo")
        self.assertEqual(resultado["origen"], "reglas")

    def test_ia_se_puede_apagar(self):
        with mock.patch.dict("os.environ", {"NLP_USAR_IA": "off"}):
            with mock.patch.object(nlp, "interpretar_con_ia") as llamada:
                with mock.patch.object(nlp, "detect_category", return_value={"id": 1, "nombre": "Alimentación"}):
                    with mock.patch.object(nlp, "detect_account", return_value={"id": 1, "nombre": "Efectivo"}):
                        nlp.interpret(self.conn, 7, "gasté 20000 en almuerzo")
        llamada.assert_not_called()


if __name__ == "__main__":
    unittest.main()
