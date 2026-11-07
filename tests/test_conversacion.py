"""Pruebas del controlador conversacional y las confirmaciones por voz.

Se usa la API real con una base temporal. El interprete LLM se apaga para que
las pruebas sean deterministas; el respaldo por reglas debe bastar.
"""

import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from backend import conversation, services
from backend.server import create_app


class MontosHabladosTests(unittest.TestCase):
    def test_montos_naturales_sin_simbolos_ni_puntos(self):
        self.assertEqual(conversation._monto_hablado(0), "cero pesos")
        self.assertEqual(conversation._monto_hablado(500), "500 pesos")
        self.assertEqual(conversation._monto_hablado(1500), "mil 500 pesos")
        self.assertEqual(conversation._monto_hablado(20000), "20 mil pesos")
        self.assertEqual(conversation._monto_hablado(21500), "21 mil 500 pesos")
        self.assertEqual(conversation._monto_hablado(1000000), "un millón de pesos")
        self.assertEqual(conversation._monto_hablado(1500000), "un millón 500 mil pesos")
        self.assertEqual(conversation._monto_hablado(-15000), "menos 15 mil pesos")
        for monto in (0, 500, 1500, 20000, 21500, 1000000, 1500000, -15000):
            texto = conversation._monto_hablado(monto)
            self.assertNotIn("$", texto)
            self.assertNotIn(".", texto)

    def test_texto_para_voz_limpia_el_mensaje_de_pantalla(self):
        limpio = conversation._texto_para_voz(
            "Entendí un GASTO de $20.000 en Alimentación."
        )
        self.assertEqual(limpio, "Entendí un gasto de 20000 en Alimentación.")

    def test_fecha_hablada(self):
        self.assertEqual(
            conversation._fecha_hablada("2027-12-31"),
            "31 de diciembre de 2027",
        )


class ConversationTests(unittest.TestCase):
    def setUp(self):
        conversation.limpiar_sesiones()
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "test.db"
        self.app = create_app(str(self.db_path))
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        self.patch = mock.patch.dict(os.environ, {"NLP_USAR_IA": "off"})
        self.patch.start()
        self.user = self.register("voz@example.com")

    def tearDown(self):
        self.patch.stop()
        conversation.limpiar_sesiones()
        self.temp.cleanup()

    def register(self, email):
        response = self.client.post(
            "/api/v1/auth/register",
            json={"nombre": "Ana", "correo": email, "password": "secreto123"},
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        payload = response.get_json()["data"]
        return {"headers": {"Authorization": "Bearer " + payload["tokens"]["access_token"]}}

    def decir(self, texto, message_id=None):
        body = {"texto": texto}
        if message_id:
            body["message_id"] = message_id
        response = self.client.post(
            "/api/v1/messages", json=body, headers=self.user["headers"]
        )
        self.assertIn(response.status_code, (200, 201), response.get_json())
        return response.get_json()["data"]

    def home(self):
        return self.client.get("/api/v1/home", headers=self.user["headers"]).get_json()["data"]

    def crear_meta(self, nombre="Mi nuevo celular", monto=500000):
        response = self.client.post(
            "/api/v1/goals",
            json={
                "nombre": nombre,
                "monto_meta": monto,
                "fecha_limite": "2027-12-31",
                "frecuencia_ahorro": "mensual",
                "aporte_periodico": 50000,
                "prioridad": 3,
            },
            headers=self.user["headers"],
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["data"]

    # --- Confirmaciones -------------------------------------------------
    def test_movimiento_pendiente_y_confirmacion_natural(self):
        respuesta = self.decir("gasté 12.000 en almuerzo", "voz-1")
        self.assertEqual(respuesta["intent"], "registrar")
        self.assertTrue(respuesta["requiere_confirmacion"])
        self.assertEqual(respuesta["estado_conversacion"], "confirmando_movimiento")
        self.assertEqual(respuesta["transacciones"][0]["estado"], "pendiente")
        self.assertIn("¿Registro", respuesta["mensaje_nancy"])
        self.assertIn("¿Registro un gasto de 12 mil pesos en alimentación?", respuesta["texto_voz"])
        self.assertNotIn("$", respuesta["texto_voz"])
        self.assertNotIn(".000", respuesta["texto_voz"])

        confirmado = self.decir("sí, está correcto")
        self.assertFalse(confirmado["requiere_confirmacion"])
        self.assertEqual(confirmado["tipo_respuesta"], "resultado")
        self.assertEqual(confirmado["estado_conversacion"], "inactiva")
        self.assertEqual(self.home()["hoy"]["gastos"], 12000)

    def test_confirmacion_con_ok(self):
        self.decir("gasté 20 mil en transporte")
        respuesta = self.decir("ok")
        self.assertEqual(respuesta["tipo_respuesta"], "resultado")
        self.assertEqual(self.home()["hoy"]["gastos"], 20000)

    def test_cancelacion_descarta_el_pendiente(self):
        pendiente = self.decir("gasté 30 mil en comida")
        respuesta = self.decir("no, cancela")
        self.assertEqual(respuesta["tipo_respuesta"], "resultado")
        self.assertEqual(self.home()["hoy"]["gastos"], 0)
        mensaje = self.client.get(
            f"/api/v1/messages/{pendiente['id']}", headers=self.user["headers"]
        ).get_json()["data"]
        self.assertEqual(mensaje["estado"], "descartado")

    def test_correccion_de_monto_antes_de_confirmar(self):
        self.decir("gasté 12.000 en almuerzo")
        correccion = self.decir("cambia el monto a 15 mil")
        self.assertTrue(correccion["requiere_confirmacion"])
        self.assertEqual(correccion["transacciones"][0]["monto"], 15000)
        self.decir("correcto")
        self.assertEqual(self.home()["hoy"]["gastos"], 15000)

    def test_confirmar_sin_pendiente_no_escribe(self):
        respuesta = self.decir("sí")
        self.assertEqual(respuesta["tipo_respuesta"], "aclaracion")
        self.assertIn("nada pendiente", respuesta["mensaje_nancy"])
        self.assertEqual(self.home()["hoy"]["gastos"], 0)

    # --- Metas ----------------------------------------------------------
    def test_ahorro_se_asocia_a_la_meta_del_usuario(self):
        meta = self.crear_meta()
        respuesta = self.decir("ahorré 50 mil para mi meta de mi nuevo celular")
        self.assertEqual(respuesta["transacciones"][0]["tipo"], "ahorro")
        self.assertEqual(respuesta["transacciones"][0]["meta_id"], meta["meta_id"])
        self.assertEqual(respuesta["transacciones"][0]["monto"], 50000)

        self.decir("sí")
        metas = self.client.get("/api/v1/goals", headers=self.user["headers"]).get_json()["data"]
        objetivo = [m for m in metas if m["meta_id"] == meta["meta_id"]][0]
        self.assertEqual(objetivo["ahorrado"], 50000)

    def test_meta_inexistente_pide_aclaracion_sin_escribir(self):
        self.crear_meta(nombre="Viaje")
        respuesta = self.decir("ahorré 50 mil para mi meta de unos audífonos")
        self.assertEqual(respuesta["tipo_respuesta"], "aclaracion")
        self.assertIn("No encontré la meta", respuesta["mensaje_nancy"])
        self.assertEqual(self.home()["hoy"]["ahorro"], 0)

    # --- Creacion de metas por dialogo ---------------------------------
    def test_meta_por_dialogo_solo_se_crea_al_confirmar(self):
        perfil = self.client.patch(
            "/api/v1/me/profile",
            json={"ingreso_trabajo_mensual": 2000000},
            headers=self.user["headers"],
        )
        self.assertEqual(perfil.status_code, 200, perfil.get_json())
        respuesta = self.decir("quiero crear una meta para comprar unos audífonos")
        self.assertEqual(respuesta["intent"], "crear_meta")
        self.assertEqual(respuesta["estado_conversacion"], "recopilando_meta")
        self.assertIn("Cuánto cuesta", respuesta["mensaje_nancy"])
        metas = self.client.get("/api/v1/goals", headers=self.user["headers"]).get_json()["data"]
        self.assertEqual(metas, [])

        self.decir("500 mil")
        self.decir("en cinco meses")
        self.decir("mensual")
        propuesta = self.decir("prioridad alta")
        self.assertTrue(propuesta["requiere_confirmacion"])
        self.assertEqual(propuesta["estado_conversacion"], "confirmando_meta")
        self.assertEqual(propuesta["datos"]["borrador"]["monto_meta"], 500000)
        self.assertEqual(propuesta["datos"]["borrador"]["prioridad"], 1)
        self.assertIn("plan recomienda", propuesta["mensaje_nancy"].lower())
        self.assertIn("¿La creo?", propuesta["mensaje_nancy"])

        # Todavia no se ha guardado.
        metas = self.client.get("/api/v1/goals", headers=self.user["headers"]).get_json()["data"]
        self.assertEqual(metas, [])

        confirmacion = self.decir("sí, está correcto")
        self.assertEqual(confirmacion["tipo_respuesta"], "resultado")
        self.assertEqual(confirmacion["datos"]["meta"]["nombre"], "audifonos")
        metas = self.client.get("/api/v1/goals", headers=self.user["headers"]).get_json()["data"]
        self.assertEqual(len(metas), 1)
        self.assertEqual(metas[0]["monto_meta"], 500000)

    def test_meta_por_dialogo_se_puede_cancelar(self):
        self.decir("quiero crear una meta para comprar audífonos")
        self.decir("500 mil")
        self.decir("cancela")
        metas = self.client.get("/api/v1/goals", headers=self.user["headers"]).get_json()["data"]
        self.assertEqual(metas, [])

    # --- Consultas naturales -------------------------------------------
    def test_consulta_de_balance_del_dia(self):
        self.decir("gasté 20 mil en almuerzo")
        self.decir("sí")
        respuesta = self.decir("¿cómo me fue hoy?")
        self.assertEqual(respuesta["tipo_respuesta"], "consulta")
        self.assertIn("$20.000", respuesta["mensaje_nancy"])
        self.assertIn("20 mil pesos", respuesta["texto_voz"])
        self.assertNotIn("$", respuesta["texto_voz"])
        self.assertEqual(respuesta["datos"]["periodo"], "hoy")

    def test_consulta_de_balance_semanal_y_mensual(self):
        self.decir("gasté 20 mil en almuerzo")
        self.decir("sí")
        semanal = self.decir("balance de esta semana")
        self.assertEqual(semanal["datos"]["periodo"], "semana")
        self.assertIn("$20.000", semanal["mensaje_nancy"])
        mensual = self.decir("¿cuánto gasté este mes?")
        self.assertEqual(mensual["datos"]["periodo"], "mes")

    def test_registrar_con_fecha_de_ayer(self):
        hoy = date.fromisoformat(services.local_date())
        ayer = (hoy - timedelta(days=1)).isoformat()
        respuesta = self.decir("gasté 20 mil en almuerzo ayer")
        self.assertEqual(respuesta["intent"], "registrar")
        self.assertEqual(respuesta["transacciones"][0]["fecha_local"], ayer)
        self.assertIn("con fecha de ayer", respuesta["texto_voz"])
        self.decir("sí")
        consulta = self.decir("¿cuánto gasté ayer?")
        self.assertEqual(consulta["datos"]["rango"]["desde"], ayer)
        self.assertEqual(consulta["datos"]["rango"]["etiqueta"], "ayer")
        self.assertIn("Ayer registraste", consulta["mensaje_nancy"])
        self.assertIn("$20.000", consulta["mensaje_nancy"])
        self.assertIsNone(consulta["datos"]["resumen"]["cupo_restante"])
        self.assertNotIn("cupo diario", consulta["texto_voz"])

    def test_gaste_ayer_sin_monto_es_consulta_con_lista(self):
        self.decir("gasté 20 mil en almuerzo ayer")
        self.decir("sí")
        respuesta = self.decir("gasté ayer")
        self.assertEqual(respuesta["intent"], "consultar_movimientos")
        self.assertEqual(respuesta["tipo_respuesta"], "consulta")
        self.assertEqual(respuesta["datos"]["rango"]["etiqueta"], "ayer")
        self.assertEqual(len(respuesta["datos"]["movimientos"]), 1)
        self.assertEqual(respuesta["datos"]["resumen"]["total_gastos"], 20000)
        self.assertIn("Gastos: 20 mil pesos", respuesta["texto_voz"])
        self.assertIn("$20.000", respuesta["mensaje_nancy"])

    def test_movimientos_de_un_rango_con_fecha(self):
        hoy = date.fromisoformat(services.local_date())
        fin_mes = hoy.replace(day=1) - timedelta(days=1)
        inicio_mes = fin_mes.replace(day=1)
        dia = inicio_mes.replace(day=2)
        mes = conversation.MESES_HABLADOS[dia.month - 1]
        self.decir(f"gasté 15 mil en comida el 2 de {mes} de {dia.year}")
        self.decir("sí")
        respuesta = self.decir(
            f"movimientos del 2 al 3 de {mes} de {dia.year}"
        )
        self.assertEqual(respuesta["intent"], "consultar_movimientos")
        self.assertEqual(respuesta["datos"]["rango"]["alcance"], "rango")
        self.assertEqual(respuesta["datos"]["rango"]["desde"], dia.isoformat())
        self.assertEqual(len(respuesta["datos"]["movimientos"]), 1)
        self.assertIn("Gastos: 15 mil pesos", respuesta["texto_voz"])

    def test_fecha_futura_no_se_registra(self):
        anio = date.fromisoformat(services.local_date()).year + 1
        respuesta = self.decir(f"gasté 20 mil en almuerzo el 1 de enero de {anio}")
        self.assertEqual(respuesta["tipo_respuesta"], "aclaracion")
        self.assertIn("futura", respuesta["mensaje_nancy"])

    def test_consulta_de_metas_y_plan(self):
        self.crear_meta()
        metas = self.decir("¿cómo van mis metas?")
        self.assertEqual(metas["intent"], "consultar_metas")
        self.assertIn("Mi nuevo celular", metas["mensaje_nancy"])
        plan = self.decir("¿cuánto debo ahorrar este mes?")
        self.assertEqual(plan["intent"], "consultar_plan")
        self.assertIn("plan recomienda", plan["mensaje_nancy"])

    def test_consultas_de_catalogo(self):
        self.assertIn("cuentas", self.decir("¿cuáles son mis cuentas?").get("mensaje_nancy", "").lower())
        self.assertEqual(self.decir("mis categorías").get("intent"), "consultar_categorias")
        self.assertEqual(self.decir("mis movimientos").get("intent"), "consultar_movimientos")
        self.assertEqual(self.decir("mi presupuesto").get("intent"), "consultar_presupuesto")
        self.assertEqual(self.decir("mi perfil").get("intent"), "consultar_perfil")

    # --- Otras operaciones por voz -------------------------------------
    def test_crear_cuenta_por_voz(self):
        propuesta = self.decir("crea una cuenta llamada Ahorros de tipo cuenta de ahorros")
        self.assertTrue(propuesta["requiere_confirmacion"])
        self.assertEqual(propuesta["datos"]["accion"]["tipo"], "crear_cuenta")
        self.decir("sí")
        cuentas = self.client.get("/api/v1/accounts", headers=self.user["headers"]).get_json()["data"]
        self.assertTrue(any(cuenta["nombre"] == "ahorros" for cuenta in cuentas))

    def test_crear_categoria_por_voz(self):
        propuesta = self.decir("crea una categoría llamada Mascotas de gasto")
        self.assertEqual(propuesta["datos"]["accion"]["tipo"], "crear_categoria")
        self.decir("ok")
        categorias = self.client.get("/api/v1/categories", headers=self.user["headers"]).get_json()["data"]
        self.assertTrue(any(categoria["nombre"] == "mascotas" for categoria in categorias))

    def test_actualizar_presupuesto_por_voz(self):
        propuesta = self.decir("cambia mi presupuesto diario a 30 mil")
        self.assertEqual(propuesta["datos"]["accion"]["tipo"], "actualizar_presupuesto")
        self.decir("sí")
        self.assertEqual(self.home()["hoy"]["presupuesto_diario"], 30000)

    def test_actualizar_ingreso_por_voz(self):
        propuesta = self.decir("mi ingreso mensual es 2 millones")
        self.assertEqual(propuesta["datos"]["accion"]["tipo"], "actualizar_perfil")
        self.decir("sí")
        perfil = self.client.get("/api/v1/me/profile", headers=self.user["headers"]).get_json()["data"]
        self.assertEqual(perfil["perfil"]["ingreso_trabajo_mensual"], 2000000)

    def test_eliminar_movimiento_por_voz(self):
        self.decir("gasté 20 mil en almuerzo")
        self.decir("sí")
        propuesta = self.decir("elimina el último movimiento")
        self.assertEqual(propuesta["datos"]["accion"]["tipo"], "eliminar_movimiento")
        self.decir("sí")
        self.assertEqual(self.home()["hoy"]["gastos"], 0)

    def test_eliminar_meta_por_voz(self):
        self.crear_meta(nombre="Viaje")
        propuesta = self.decir("elimina la meta Viaje")
        self.assertEqual(propuesta["datos"]["accion"]["tipo"], "eliminar_meta")
        self.decir("sí")
        metas = self.client.get("/api/v1/goals", headers=self.user["headers"]).get_json()["data"]
        self.assertEqual(metas, [])

    def test_meta_sin_capacidad_explica_por_que(self):
        """Con ingreso sin declarar el LP no asigna: Nancy debe decirlo."""
        self.decir("quiero crear una meta para comprar unos audífonos")
        self.decir("500 mil")
        self.decir("en cinco meses")
        self.decir("mensual")
        propuesta = self.decir("prioridad alta")
        self.assertIn("plan todavía no puede", propuesta["mensaje_nancy"])
        self.assertNotIn("$0", propuesta["mensaje_nancy"])
        self.assertNotIn("0 %", propuesta["mensaje_nancy"])

    def test_mensaje_duplicado_no_procesa_dos_veces(self):
        primero = self.decir("gasté 12.000 en almuerzo", "repetido-1")
        segundo = self.decir("otra cosa", "repetido-1")
        self.assertTrue(segundo["duplicado"])
        self.assertEqual(primero["id"], segundo["id"])
        self.assertEqual(self.home()["hoy"]["gastos"], 0)  # sigue pendiente


if __name__ == "__main__":
    unittest.main()
