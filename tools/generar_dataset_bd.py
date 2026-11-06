"""Genera el dataset demo completo de FinaGotchi dentro de ``finagotchi.db``.

Uso:
    py -3 tools/generar_dataset_bd.py
    py -3 tools/generar_dataset_bd.py --transacciones 500 --semilla 20261104
    py -3 tools/generar_dataset_bd.py --db C:\\ruta\\copia.db --no-exportar

El generador hace, en este orden:

1. Respalda la base actual en ``backups/`` (salvo ``--sin-respaldo``).
2. Borra los datos de prueba de todas las tablas de negocio. Conserva las
   plantillas (``plantilla_*``) y ``schema_migrations``.
3. Crea usuarios, dispositivos, movimientos, mensajes, interacciones de IA,
   metas, presupuestos, cierres, puntos, salud, alertas, telemetria,
   notificaciones, comandos, sesiones y casos limite.
4. Comprueba ``PRAGMA foreign_key_check`` e ``integrity_check``.
5. Exporta un CSV por tabla y un ``manifest.json``.

El reparto por defecto es 25 usuarios / 18 dispositivos / 500 transacciones:
un usuario nunca tiene mas de un dispositivo y siempre hay menos dispositivos
que usuarios. Los usuarios sin dispositivo usan solo la app.

La generacion es reproducible con la misma semilla (las fechas se calculan
respecto al dia de ejecucion).
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
import random
import shutil
import sqlite3
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import init_db  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

BOGOTA_UTC_OFFSET = timedelta(hours=5)
HORA_CIERRE = time(21, 30)
IDIOMA = "es-CO"

TABLAS_DATOS = (
    "alertas_log",
    "categoria_palabras",
    "categorias",
    "cierres_dia",
    "consentimientos",
    "cuenta_palabras",
    "cuentas",
    "dispositivos",
    "dispositivos_comandos",
    "dispositivos_notificaciones",
    "dispositivos_telemetria",
    "estado_mascota",
    "gastos_fijos",
    "interacciones_ia",
    "mensajes_dispositivo",
    "metas",
    "metas_eventos",
    "perfil_financiero",
    "perfil_secciones",
    "preferencias_notificacion",
    "presupuesto_categoria",
    "presupuesto_diario_historial",
    "presupuestos",
    "progreso_etapa",
    "puntos_log",
    "retos_respuestas",
    "salud_log",
    "sesiones_refresco",
    "solicitudes_eliminacion_cuenta",
    "tokens_recuperacion",
    "tokens_verificacion_correo",
    "transacciones",
    "transacciones_versiones",
    "usuarios",
    "vinculacion_codigos",
)

PERSONAS = (
    ("Simulador", "Simulador de pruebas", "prefiero_no_decir", 30, "trabajo"),
    ("Valentina", "Valentina Rios", "mujer", 21, "estudio"),
    ("Santiago", "Santiago Perez", "hombre", 24, "estudio_y_trabajo"),
    ("Camila", "Camila Rodriguez", "mujer", 28, "trabajo"),
    ("Andres", "Andres Gomez", "hombre", 22, "estudio"),
    ("Laura", "Laura Martinez", "mujer", 26, "trabajo"),
    ("Daniel", "Daniel Herrera", "hombre", 31, "trabajo"),
    ("Sofia", "Sofia Torres", "mujer", 19, "estudio"),
    ("Mateo", "Mateo Ramirez", "hombre", 23, "estudio_y_trabajo"),
    ("Isabella", "Isabella Cruz", "mujer", 25, "trabajo"),
    ("Sebastian", "Sebastian Diaz", "hombre", 20, "estudio"),
    ("Mariana", "Mariana Vargas", "mujer", 29, "trabajo"),
    ("Nicolas", "Nicolas Castro", "hombre", 27, "trabajo"),
    ("Gabriela", "Gabriela Moreno", "mujer", 22, "estudio_y_trabajo"),
    ("Felipe", "Felipe Rojas", "hombre", 33, "trabajo"),
    ("Daniela", "Daniela Jimenez", "mujer", 24, "estudio"),
    ("Juan Pablo", "Juan Pablo Ortiz", "hombre", 21, "estudio"),
    ("Manuela", "Manuela Suarez", "mujer", 30, "trabajo"),
    ("Esteban", "Esteban Navarro", "hombre", 26, "trabajo"),
    ("Sara", "Sara Molina", "mujer", 23, "estudio_y_trabajo"),
    ("Alejandro", "Alejandro Reyes", "hombre", 35, "trabajo"),
    ("Paula", "Paula Cardenas", "mujer", 20, "estudio"),
    ("Ricardo", "Ricardo Pena", "hombre", 28, "trabajo"),
    ("Juliana", "Juliana Acosta", "mujer", 25, "estudio_y_trabajo"),
    ("Tomas", "Tomas Guerrero", "hombre", 32, "trabajo"),
)

LOCALIDADES = (
    "Chapinero", "Suba", "Kennedy", "Usaquen", "Engativa", "Bosa",
    "Teusaquillo", "Fontibon", "Ciudad Bolivar", "Puente Aranda",
)

PESOS_GASTO = {
    "Alimentacion": 30, "Alimentación": 30, "Transporte": 15,
    "Familia y detalles": 6, "Ocio y gustos": 10,
    "Vivienda y fijos": 12, "Suscripciones": 5, "Salud y aseo": 6,
    "Deudas": 4, "Finanzas": 3, "Prestamos": 2, "Préstamos": 2,
    "Ahorro e inversion": 2, "Ahorro e inversión": 2, "Otros": 5,
    "Mascotas": 4, "Delivery": 5, "Educacion": 3, "Educación": 3,
}

BASES_GASTO = {
    "Alimentacion": 18000, "Alimentación": 18000, "Transporte": 9000,
    "Familia y detalles": 35000, "Ocio y gustos": 30000,
    "Vivienda y fijos": 110000, "Suscripciones": 22000,
    "Salud y aseo": 20000, "Deudas": 80000, "Finanzas": 12000,
    "Prestamos": 70000, "Préstamos": 70000,
    "Ahorro e inversion": 50000, "Ahorro e inversión": 50000,
    "Otros": 15000, "Mascotas": 25000, "Delivery": 22000,
    "Educacion": 40000, "Educación": 40000,
}

CONCEPTOS = {
    "Alimentacion": ("almuerzo", "desayuno", "mercado", "cafe", "panaderia", "restaurante", "domicilio de comida"),
    "Alimentación": ("almuerzo", "desayuno", "mercado", "cafe", "panaderia", "restaurante", "domicilio de comida"),
    "Transporte": ("pasaje de bus", "TransMilenio", "taxi", "Uber", "gasolina", "parqueadero"),
    "Familia y detalles": ("regalo para mama", "detalle de cumpleanos", "cine familiar", "mercado de la casa"),
    "Ocio y gustos": ("cine", "salida con amigos", "videojuego", "concierto", "libro"),
    "Vivienda y fijos": ("arriendo", "servicios publicos", "internet", "administracion", "reparacion"),
    "Suscripciones": ("Netflix", "Spotify", "plan de datos", "YouTube Premium"),
    "Salud y aseo": ("farmacia", "cita medica", "gimnasio", "corte de cabello", "jabon"),
    "Deudas": ("cuota de la tarjeta", "pago de credito", "cuota del celular"),
    "Finanzas": ("comision bancaria", "envio de dinero", "retiro"),
    "Prestamos": ("prestamo a un amigo", "cuota del prestamo"),
    "Ahorro e inversion": ("ahorro", "inversion", "fondo"),
    "Otros": ("compra pequena", "varios", "imprevisto"),
    "Mascotas": ("comida del gato", "veterinario", "arena del gato"),
    "Delivery": ("domicilio", "Rappi", "pedido de comida"),
    "Educacion": ("matricula", "curso", "libros"),
    "Educación": ("matricula", "curso", "libros"),
    "Trabajo": ("salario", "pago de freelance", "honorarios"),
    "Apoyo familiar": ("mesada", "apoyo de mis papas", "ayuda familiar"),
    "Beca": ("beca", "estipendio de la universidad"),
    "Otros ingresos": ("venta de algo", "reembolso", "regalo"),
}

META_NOMBRES = (
    "Viaje a Santa Marta", "Nuevo celular", "Fondo de emergencia",
    "Bicicleta", "Curso de ingles", "Laptop", "Mudanza", "Concierto",
    "Ahorro navideno", "Reparar el celular", "Beca de intercambio",
    "Moto", "Muebles para el cuarto", "Fondo para estudiar",
)

CUENTAS_EXTRA = (
    ("Tarjeta Nu", "tarjeta"),
    ("Tarjeta Davivienda", "tarjeta"),
    ("Ahorros UVR", "cuenta_ahorros"),
    ("Caja menor", "efectivo"),
)

CATEGORIAS_EXTRA = (
    ("Mascotas", "gasto", ("mascota", "gato", "perro", "veterinario")),
    ("Delivery", "gasto", ("delivery", "rappi", "domicilio")),
    ("Educacion", "gasto", ("curso", "matricula", "universidad")),
    ("Freelance", "ingreso", ("freelance", "cliente", "proyecto")),
)


def _iso_utc(dt_local: datetime) -> str:
    """Convierte una hora local de Bogota a la cadena UTC que usa la base."""
    return (dt_local + BOGOTA_UTC_OFFSET).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dt_local(fecha: date, hora: time) -> datetime:
    return datetime.combine(fecha, hora)


def _redondear(monto: float, paso: int = 500) -> int:
    return max(paso, int(round(monto / paso)) * paso)


def _json(datos) -> str:
    return json.dumps(datos, ensure_ascii=False, separators=(",", ":"))


class Generador:
    """Construye el dataset dentro de una conexion SQLite ya abierta."""

    def __init__(self, conn, *, usuarios, dispositivos, transacciones, dias,
                 semilla, hoy: date | None = None):
        self.conn = conn
        self.rng = random.Random(semilla)
        self.total_usuarios = max(1, usuarios)
        self.total_dispositivos = max(0, min(dispositivos, usuarios))
        self.total_transacciones = max(1, transacciones)
        self.dias = max(7, dias)
        self.semilla = semilla
        self.hoy = hoy or datetime.now().date()
        self.start = self.hoy - timedelta(days=self.dias - 1)

        self.planes: list[dict] = []
        self.catalogo: dict[int, dict] = {}
        self.metas: dict[int, list[dict]] = {}
        self.presupuestos: dict[int, dict] = {}
        self.dispositivos: dict[int, dict] = {}
        self.historial: dict[int, list[tuple[date, int]]] = {}
        self.salud: dict[int, int] = {}
        self.txs: dict[int, list[dict]] = {}
        self.mensajes: dict[int, list[dict]] = {}

    # ------------------------------------------------------------------
    # Orquestacion
    # ------------------------------------------------------------------
    def ejecutar(self) -> dict:
        self._limpiar()
        self._crear_usuarios()
        self._crear_catalogos()
        self._crear_metas()
        self._crear_finanzas_fijas()
        self._crear_dispositivos()
        self._asignar_transacciones()
        for plan in self.planes:
            self._insertar_movimientos(plan)
        self._crear_interacciones()
        self._completar_metas_y_puntos()
        self._crear_cierres_y_salud()
        self._actualizar_progreso()
        self._crear_alertas()
        self._crear_notificaciones_telemetria_comandos()
        self._crear_cuenta_y_seguridad()
        self.conn.commit()
        self._verificar()
        return self.resumen()

    def _limpiar(self) -> None:
        self.conn.commit()
        self.conn.execute("PRAGMA foreign_keys = OFF")
        for tabla in TABLAS_DATOS:
            self.conn.execute(f"DELETE FROM {tabla}")
        try:
            marcas = ",".join("?" * len(TABLAS_DATOS))
            self.conn.execute(
                f"DELETE FROM sqlite_sequence WHERE name IN ({marcas})",
                TABLAS_DATOS,
            )
        except sqlite3.OperationalError:
            pass
        self.conn.commit()
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()

    # ------------------------------------------------------------------
    # Usuarios y perfiles
    # ------------------------------------------------------------------
    def _plan_usuario(self, idx: int, persona: tuple) -> dict:
        rng = self.rng
        nombre, completo, genero, edad, ocupacion = persona
        if ocupacion == "estudio":
            trabajo = rng.choice([0, 0, 0, 350000, 600000])
            apoyo = rng.randrange(300000, 1000001, 50000)
            beca = rng.choice([0, 0, 250000, 500000, 750000])
            frecuencia = rng.choice(["mensual", "irregular"])
        elif ocupacion == "estudio_y_trabajo":
            trabajo = rng.randrange(900000, 2200001, 50000)
            apoyo = rng.choice([0, 150000, 300000, 450000])
            beca = rng.choice([0, 0, 250000])
            frecuencia = rng.choice(["quincenal", "mensual"])
        else:
            trabajo = rng.randrange(1800000, 6500001, 100000)
            apoyo = rng.choice([0, 0, 0, 200000, 400000])
            beca = 0
            frecuencia = rng.choice(["quincenal", "mensual"])

        otros = rng.choice([0, 0, 50000, 120000, 250000])
        ingreso_total = trabajo + apoyo + beca + otros
        factor = rng.uniform(0.45, 0.8)
        presupuesto = _redondear(ingreso_total / 30 * factor, 1000)
        presupuesto = max(10000, min(presupuesto, 180000))

        if idx == 0:
            presupuesto = 45000
            correo = "simulador@finagotchi.local"
            password = "simulador123"
        else:
            correo = f"demo{idx:02d}@finagotchi.local"
            password = "Demo1234"

        deuda = rng.choice([0, 0, 0, 250000, 800000, 1500000])
        estres = rng.randint(2, 8)
        if deuda >= 800000:
            estres = min(10, estres + 2)
        ahorro = rng.choice([0, 50000, 100000, 200000, 350000]) if ingreso_total else 0

        perfil = {
            "edad": edad,
            "genero": genero,
            "localidad": rng.choice(LOCALIDADES),
            "ocupacion": ocupacion,
            "nivel_educativo": rng.choice(
                ["secundaria", "tecnico", "universitario", "posgrado"]
                if ocupacion == "trabajo" else ["secundaria", "universitario"]
            ),
            "con_quien_vive": rng.choice(["familia", "solo", "companeros", "otra"]),
            "tiene_ingresos_propios": 1 if trabajo else 0,
            "ingreso_trabajo_mensual": trabajo,
            "apoyo_familiar_mensual": apoyo,
            "beca_mensual": beca,
            "otros_ingresos_mensual": otros,
            "frecuencia_ingreso": frecuencia,
            "estilo_control": rng.choice(["de_memoria", "algunas_veces", "riguroso"]),
            "gasto_total_mensual_estimado": int(ingreso_total * rng.uniform(0.55, 0.95)),
            "frecuencia_compras_impulsivas": rng.choice(
                ["casi_nunca", "a_veces", "seguido", "siempre"]
            ),
            "num_suscripciones": rng.randint(0, 6),
            "gasto_suscripciones_mensual": 0,
            "pedidos_domicilio_mes": rng.randint(0, 18),
            "gasto_domicilios_mensual": 0,
            "registros_estimados_semana": rng.randint(1, 14),
            "usa_app_presupuesto": rng.choice([0, 1, 1]),
            "anota_gastos_manual": rng.choice([0, 1]),
            "dificultad_llevar_cuentas": rng.randint(1, 5),
            "tiene_deuda_tarjeta": 1 if deuda else 0,
            "saldo_deuda_tarjeta": deuda,
            "paga_a_cuotas": 1 if deuda and rng.random() < 0.6 else 0,
            "ahorro_mensual": ahorro,
            "tiene_fondo_emergencia": rng.choice([0, 0, 1]),
            "estres_financiero": estres,
            "se_siente_seguro": rng.choice([0, 1, 1]),
        }
        perfil["gasto_suscripciones_mensual"] = perfil["num_suscripciones"] * rng.randrange(
            12000, 46000, 1000
        )
        perfil["gasto_domicilios_mensual"] = perfil["pedidos_domicilio_mes"] * rng.randrange(
            15000, 45000, 1000
        )

        return {
            "idx": idx,
            "nombre": nombre,
            "nombre_completo": completo,
            "genero": genero,
            "ocupacion": ocupacion,
            "correo": correo,
            "password": password,
            "presupuesto": presupuesto,
            "trabajo": trabajo,
            "apoyo": apoyo,
            "beca": beca,
            "otros": otros,
            "ingreso_total": ingreso_total,
            "frecuencia": frecuencia,
            "perfil": perfil,
            "device_uid": None,
            "n_tx": 0,
        }

    def _crear_usuarios(self) -> None:
        hash_demo = generate_password_hash("Demo1234")
        hash_sim = generate_password_hash("simulador123")
        for idx in range(self.total_usuarios):
            persona = PERSONAS[idx] if idx < len(PERSONAS) else (
                f"Usuario {idx + 1}", f"Usuario Demo {idx + 1}",
                "prefiero_no_decir", 20 + idx % 15, "trabajo",
            )
            plan = self._plan_usuario(idx, persona)
            creado = self.start - timedelta(days=self.rng.randint(20, 400))
            ultimo = self.hoy - timedelta(days=self.rng.randint(0, 5))
            plan["creado"] = datetime.combine(creado, time(9, 0))
            password_hash = hash_sim if idx == 0 else hash_demo
            cur = self.conn.execute(
                """
                INSERT INTO usuarios
                    (nombre, nombre_completo, correo, correo_verificado,
                     telefono, proveedor_auth, password_hash, presupuesto_diario,
                     moneda, zona_horaria, estado, ultimo_acceso,
                     creado_en, actualizado_en)
                VALUES (?, ?, ?, 1, ?, 'correo', ?, ?, 'COP', 'America/Bogota',
                        'activo', ?, ?, ?)
                """,
                (
                    plan["nombre"], plan["nombre_completo"], plan["correo"],
                    f"+57 3{self.rng.randint(100000000, 999999999)}",
                    password_hash, plan["presupuesto"],
                    _iso_utc(datetime.combine(ultimo, time(20, 0))),
                    _iso_utc(plan["creado"]), _iso_utc(plan["creado"]),
                ),
            )
            plan["uid"] = cur.lastrowid
            plan["device_uid"] = (
                "FINAGOTCHI-PC-SIMULATOR-01" if idx == 0 else f"FG-{idx:04d}"
            ) if idx < self.total_dispositivos else None
            self.planes.append(plan)
            self.salud[plan["uid"]] = 100
            self._actualizar_perfil(plan)

    def _actualizar_perfil(self, plan: dict) -> None:
        uid = plan["uid"]
        perfil = plan["perfil"]
        columnas = ", ".join(f"{c} = ?" for c in perfil)
        self.conn.execute(
            f"UPDATE perfil_financiero SET {columnas}, actualizado_en = ? WHERE usuario_id = ?",
            (*perfil.values(), _iso_utc(plan["creado"]), uid),
        )

        self.conn.execute(
            """
            UPDATE preferencias_notificacion
               SET recordatorio_hora = ?, avisos_presupuesto = ?,
                   avisos_metas = ?, avisos_dispositivo = ?, modo_silencio = ?
             WHERE usuario_id = ?
            """,
            (
                f"{self.rng.randint(19, 22):02d}:00",
                self.rng.choice([1, 1, 0]),
                self.rng.choice([1, 1, 0]),
                1 if plan["device_uid"] else 0,
                self.rng.choice([0, 0, 1]),
                uid,
            ),
        )

        incompleto = plan["idx"] in (5, 17) or (plan["idx"] % 9 == 0)
        for seccion in (
            "sobre_ti", "ingresos", "gastos_habitos",
            "como_llevas_cuentas", "deudas_ahorro", "bienestar",
        ):
            if incompleto and seccion in ("deudas_ahorro", "bienestar"):
                estado, respondidas = "pendiente", 0
            elif incompleto:
                estado, respondidas = "en_progreso", self.rng.randint(1, 3)
            else:
                estado = self.rng.choices(
                    ["completo", "en_progreso", "pendiente"], [0.8, 0.15, 0.05]
                )[0]
                respondidas = 4 if estado == "completo" else self.rng.randint(1, 3)
            self.conn.execute(
                """
                UPDATE perfil_secciones
                   SET estado = ?, preguntas_respondidas = ?, actualizado_en = ?
                 WHERE usuario_id = ? AND seccion = ?
                """,
                (estado, respondidas, _iso_utc(plan["creado"]), uid, seccion),
            )

        self.conn.execute(
            "UPDATE estado_mascota SET salud = 100, ultima_actualizacion = ? WHERE usuario_id = ?",
            (_iso_utc(plan["creado"]), uid),
        )
        self.conn.execute(
            """
            UPDATE progreso_etapa
               SET fecha_inicio_diagnostico = ?, dias_diagnostico = 28,
                   meta_puntos = ?, meta_registros = ?, actualizado_en = ?
             WHERE usuario_id = ?
            """,
            (
                plan["creado"].date().isoformat(),
                self.rng.choice([100, 150, 200]),
                max(10, plan["n_tx"] * 3 or 20),
                _iso_utc(plan["creado"]), uid,
            ),
        )

    # ------------------------------------------------------------------
    # Catalogos propios de cada usuario
    # ------------------------------------------------------------------
    def _crear_catalogos(self) -> None:
        rng = self.rng
        for plan in self.planes:
            uid = plan["uid"]
            for nombre, tipo, palabras in rng.sample(
                CATEGORIAS_EXTRA, k=rng.randint(0, 2)
            ):
                existe = self.conn.execute(
                    """
                    SELECT 1 FROM categorias
                     WHERE usuario_id = ? AND lower(nombre) = lower(?)
                    """,
                    (uid, nombre),
                ).fetchone()
                if existe:
                    continue
                orden = self.conn.execute(
                    "SELECT COALESCE(MAX(orden), 0) + 1 FROM categorias WHERE usuario_id = ?",
                    (uid,),
                ).fetchone()[0]
                cur = self.conn.execute(
                    """
                    INSERT INTO categorias
                        (usuario_id, nombre, tipo, icono, es_sistema, es_fija,
                         activa, orden, creado_en)
                    VALUES (?, ?, ?, '📦', 0, 0, 1, ?, ?)
                    """,
                    (uid, nombre, tipo, orden, _iso_utc(plan["creado"])),
                )
                cat_id = cur.lastrowid
                for palabra in palabras:
                    try:
                        self.conn.execute(
                            """
                            INSERT INTO categoria_palabras (usuario_id, categoria_id, palabra)
                            VALUES (?, ?, ?)
                            """,
                            (uid, cat_id, palabra),
                        )
                    except sqlite3.IntegrityError:
                        pass

            for nombre, tipo_cuenta in rng.sample(
                CUENTAS_EXTRA, k=rng.randint(0, 2)
            ):
                existe = self.conn.execute(
                    """
                    SELECT 1 FROM cuentas
                     WHERE usuario_id = ? AND lower(nombre) = lower(?)
                    """,
                    (uid, nombre),
                ).fetchone()
                if existe:
                    continue
                orden = self.conn.execute(
                    "SELECT COALESCE(MAX(orden), 0) + 1 FROM cuentas WHERE usuario_id = ?",
                    (uid,),
                ).fetchone()[0]
                saldo = 0 if tipo_cuenta == "tarjeta" else _redondear(
                    rng.randrange(0, 250000), 1000
                )
                cur = self.conn.execute(
                    """
                    INSERT INTO cuentas
                        (usuario_id, nombre, tipo_cuenta, icono, saldo_inicial,
                         es_sistema, es_por_defecto, oculta, orden, creado_en,
                         actualizado_en)
                    VALUES (?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?)
                    """,
                    (
                        uid, nombre, tipo_cuenta,
                        "💳" if tipo_cuenta == "tarjeta" else "🏦",
                        saldo, orden, _iso_utc(plan["creado"]),
                        _iso_utc(plan["creado"]),
                    ),
                )
                cuenta_id = cur.lastrowid
                for palabra in (nombre.lower(), nombre.lower().replace(" ", "")):
                    try:
                        self.conn.execute(
                            """
                            INSERT INTO cuenta_palabras (usuario_id, cuenta_id, palabra)
                            VALUES (?, ?, ?)
                            """,
                            (uid, cuenta_id, palabra),
                        )
                    except sqlite3.IntegrityError:
                        pass

            cats = self.conn.execute(
                """
                SELECT id, nombre, tipo FROM categorias
                 WHERE usuario_id = ? AND activa = 1
                 ORDER BY orden, id
                """,
                (uid,),
            ).fetchall()
            gastos, pesos_gasto = [], {}
            for cat in cats:
                if cat["tipo"] != "gasto":
                    continue
                peso = PESOS_GASTO.get(cat["nombre"], 3) * rng.uniform(0.4, 1.8)
                if cat["nombre"] in ("Vivienda y fijos", "Suscripciones") and plan["ingreso_total"] < 1000000:
                    peso *= 0.5
                gastos.append({"id": cat["id"], "nombre": cat["nombre"]})
                pesos_gasto[cat["id"]] = peso

            ingresos, pesos_ingreso = [], {}
            for cat in cats:
                if cat["tipo"] != "ingreso":
                    continue
                nombre = cat["nombre"]
                if nombre == "Trabajo":
                    peso = 5.0 if plan["trabajo"] else 0.4
                elif nombre == "Apoyo familiar":
                    peso = 3.0 if plan["apoyo"] else 0.3
                elif nombre == "Beca":
                    peso = 2.5 if plan["beca"] else 0.2
                elif nombre == "Freelance":
                    peso = 2.0 if plan["trabajo"] else 0.5
                else:
                    peso = 1.2
                ingresos.append({"id": cat["id"], "nombre": nombre})
                pesos_ingreso[cat["id"]] = peso * rng.uniform(0.7, 1.3)

            cuentas, pesos_cuenta = [], {}
            base_cuenta = {
                "Efectivo": 3.2, "Nequi": 3.0, "Daviplata": 2.0,
                "Nu": 1.3, "Bancolombia": 1.3,
            }
            for cuenta in self.conn.execute(
                "SELECT id, nombre, tipo_cuenta FROM cuentas WHERE usuario_id = ? ORDER BY orden, id",
                (uid,),
            ):
                cuentas.append({"id": cuenta["id"], "nombre": cuenta["nombre"]})
                pesos_cuenta[cuenta["id"]] = base_cuenta.get(
                    cuenta["nombre"], 1.6 if cuenta["tipo_cuenta"] == "tarjeta" else 1.0
                )

            self.catalogo[uid] = {
                "gastos": gastos,
                "pesos_gasto": pesos_gasto,
                "ingresos": ingresos,
                "pesos_ingreso": pesos_ingreso,
                "cuentas": cuentas,
                "pesos_cuenta": pesos_cuenta,
            }

    # ------------------------------------------------------------------
    # Metas, gastos fijos y presupuestos
    # ------------------------------------------------------------------
    def _crear_metas(self) -> None:
        rng = self.rng
        factor_ingreso = max(0.7, min(2.2, self.planes[0]["ingreso_total"] / 2_000_000 or 1))
        for plan in self.planes:
            uid = plan["uid"]
            factor = max(0.7, min(2.2, plan["ingreso_total"] / 2_000_000 or 1))
            cantidad = rng.randint(2, 4)
            lista = []
            for nombre in rng.sample(META_NOMBRES, cantidad):
                monto = _redondear(
                    rng.randrange(250000, 2500001, 50000) * factor, 1000
                )
                frecuencia = rng.choice(["semanal", "quincenal", "mensual"])
                aporte = _redondear(monto / rng.randint(8, 24), 1000)
                creado = self.start + timedelta(days=rng.randint(0, 40))
                limite = self.hoy + timedelta(days=rng.randint(45, 240))
                cur = self.conn.execute(
                    """
                    INSERT INTO metas
                        (usuario_id, nombre, icono, monto_meta, fecha_limite,
                         frecuencia_ahorro, aporte_periodico, dia_aporte,
                         hora_recordatorio, prioridad, estado, creado_en,
                         actualizado_en)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'activa', ?, ?)
                    """,
                    (
                        uid, nombre, "🎯", monto, limite.isoformat(), frecuencia,
                        aporte, rng.randint(1, 7) if frecuencia == "semanal" else None,
                        f"{rng.randint(7, 10):02d}:00", rng.randint(1, 3),
                        _iso_utc(datetime.combine(creado, time(8, 0))),
                        _iso_utc(datetime.combine(creado, time(8, 0))),
                    ),
                )
                lista.append({
                    "id": cur.lastrowid,
                    "nombre": nombre,
                    "monto": monto,
                    "aporte": aporte,
                    "frecuencia": frecuencia,
                    "creado": creado,
                })
            self.metas[uid] = lista
        self._factor_ingreso_referencia = factor_ingreso

    def _crear_finanzas_fijas(self) -> None:
        rng = self.rng
        fijos = (
            ("Arriendo", "Vivienda y fijos", 450000, 1700000, "mensual"),
            ("Internet", "Vivienda y fijos", 60000, 140000, "mensual"),
            ("Plan de celular", "Suscripciones", 30000, 90000, "mensual"),
            ("Netflix", "Suscripciones", 18000, 45000, "mensual"),
            ("Spotify", "Suscripciones", 15000, 32000, "mensual"),
            ("Gimnasio", "Salud y aseo", 60000, 170000, "mensual"),
            ("Transporte semanal", "Transporte", 25000, 80000, "semanal"),
            ("Seguro medico", "Salud y aseo", 80000, 230000, "mensual"),
        )
        self.conn.execute("DELETE FROM presupuesto_diario_historial")
        for plan in self.planes:
            uid = plan["uid"]
            catalogo = self.catalogo[uid]
            por_nombre = {c["nombre"]: c["id"] for c in catalogo["gastos"]}
            factor = max(0.6, min(2.3, plan["ingreso_total"] / 2_000_000 or 1))
            disponibles = [f for f in fijos if f[1] in por_nombre]
            for nombre, categoria, minimo, maximo, periodicidad in rng.sample(
                disponibles, k=min(len(disponibles), rng.randint(2, 4))
            ):
                monto = _redondear(rng.randrange(minimo, maximo + 1, 5000) * factor, 1000)
                self.conn.execute(
                    """
                    INSERT INTO gastos_fijos
                        (usuario_id, nombre, monto, periodicidad, dia_pago, tipo,
                         categoria_id, cuenta_id, activo, creado_en)
                    VALUES (?, ?, ?, ?, ?, 'gasto', ?, ?, 1, ?)
                    """,
                    (
                        uid, nombre, monto, periodicidad, rng.randint(1, 28),
                        por_nombre[categoria], self._cuenta_al_azar(catalogo),
                        _iso_utc(plan["creado"]),
                    ),
                )

            mes_actual = self.hoy.replace(day=1)
            inicio = self._sumar_meses(mes_actual, -2)
            fin = self._sumar_meses(mes_actual, 1) - timedelta(days=1)
            aprobado = 1 if rng.random() < 0.85 else 0
            aprobado_en = (
                _iso_utc(datetime.combine(inicio + timedelta(days=1), time(10, 0)))
                if aprobado else None
            )
            cur = self.conn.execute(
                """
                INSERT INTO presupuestos
                    (usuario_id, fecha_inicio, fecha_fin, meses, aprobado,
                     aprobado_en, creado_en)
                VALUES (?, ?, ?, 3, ?, ?, ?)
                """,
                (
                    uid, inicio.isoformat(), fin.isoformat(), aprobado,
                    aprobado_en, _iso_utc(datetime.combine(inicio, time(9, 0))),
                ),
            )
            presupuesto_id = cur.lastrowid
            limites = {}
            elegidas = min(len(catalogo["gastos"]), rng.randint(5, 8))
            for cat in rng.sample(catalogo["gastos"], elegidas):
                peso = catalogo["pesos_gasto"][cat["id"]]
                total_peso = sum(catalogo["pesos_gasto"].values()) or 1
                limite = _redondear(plan["presupuesto"] * 30 * peso / total_peso, 1000)
                self.conn.execute(
                    """
                    INSERT INTO presupuesto_categoria
                        (usuario_id, presupuesto_id, categoria_id, tipo,
                         monto_limite_mensual)
                    VALUES (?, ?, ?, 'gasto', ?)
                    """,
                    (uid, presupuesto_id, cat["id"], limite),
                )
                limites[cat["id"]] = limite
            self.presupuestos[uid] = {
                "id": presupuesto_id,
                "inicio": inicio,
                "fin": fin,
                "aprobado": aprobado,
                "categorias": limites,
            }

            inicial = _redondear(plan["presupuesto"] * rng.uniform(0.8, 1.2), 1000)
            if rng.random() < 0.65:
                self.conn.execute(
                    """
                    INSERT INTO presupuesto_diario_historial
                        (usuario_id, fecha_local, monto, motivo, creado_en, actualizado_en)
                    VALUES (?, ?, ?, 'inicial', ?, ?)
                    """,
                    (
                        uid, self.start.isoformat(), inicial,
                        _iso_utc(plan["creado"]), _iso_utc(plan["creado"]),
                    ),
                )
                fecha_ajuste = self.start + timedelta(
                    days=rng.randint(1, max(1, (self.hoy - self.start).days - 2))
                )
                self.conn.execute(
                    """
                    INSERT INTO presupuesto_diario_historial
                        (usuario_id, fecha_local, monto, motivo, creado_en, actualizado_en)
                    VALUES (?, ?, ?, 'ajuste', ?, ?)
                    """,
                    (
                        uid, fecha_ajuste.isoformat(), plan["presupuesto"],
                        _iso_utc(datetime.combine(fecha_ajuste, time(11, 0))),
                        _iso_utc(datetime.combine(fecha_ajuste, time(11, 0))),
                    ),
                )
                self.historial[uid] = [
                    (self.start, inicial), (fecha_ajuste, plan["presupuesto"]),
                ]
            else:
                self.conn.execute(
                    """
                    INSERT INTO presupuesto_diario_historial
                        (usuario_id, fecha_local, monto, motivo, creado_en, actualizado_en)
                    VALUES (?, ?, ?, 'inicial', ?, ?)
                    """,
                    (
                        uid, self.start.isoformat(), plan["presupuesto"],
                        _iso_utc(plan["creado"]), _iso_utc(plan["creado"]),
                    ),
                )
                self.historial[uid] = [(self.start, plan["presupuesto"])]

    @staticmethod
    def _sumar_meses(fecha: date, meses: int) -> date:
        total = fecha.year * 12 + (fecha.month - 1) + meses
        return date(total // 12, total % 12 + 1, 1)

    def _cuenta_al_azar(self, catalogo: dict) -> int:
        cuentas = catalogo["cuentas"]
        return self.rng.choices(
            [c["id"] for c in cuentas],
            weights=[catalogo["pesos_cuenta"][c["id"]] for c in cuentas],
            k=1,
        )[0]

    # ------------------------------------------------------------------
    # Dispositivos
    # ------------------------------------------------------------------
    def _crear_dispositivos(self) -> None:
        rng = self.rng
        for plan in self.planes:
            if not plan["device_uid"]:
                continue
            uid = plan["uid"]
            vinculado = plan["creado"] + timedelta(days=rng.randint(1, 12), hours=rng.randint(1, 8))
            estado = rng.choices(
                ["conectado", "sin_conexion", "desconectado"], [0.6, 0.3, 0.1]
            )[0]
            bateria = rng.choices(
                [rng.randint(1, 20), rng.randint(21, 60), rng.randint(61, 100)],
                [0.15, 0.35, 0.5],
            )[0]
            ultima = self.hoy - timedelta(days=rng.randint(0, 4), hours=rng.randint(0, 23))
            cur = self.conn.execute(
                """
                INSERT INTO dispositivos
                    (device_uid, usuario_id, modelo, firmware, mac_address,
                     token_hash, token_actualizado_en, metodo_vinculacion,
                     vinculado_en, estado_conexion, estado_dispositivo,
                     nivel_bateria, ultima_conexion, ultima_telemetria,
                     registros_pendientes, creado_en, actualizado_en)
                VALUES (?, ?, 'ESP32-S3-FinaGotchi', ?, ?, ?, ?, ?, ?, ?, 'reposo',
                        ?, ?, ?, 0, ?, ?)
                """,
                (
                    plan["device_uid"], uid,
                    rng.choice(["1.2.0", "1.3.1", "1.4.2"]),
                    ":".join(f"{rng.randint(0, 255):02X}" for _ in range(6)),
                    self._token_hex(), _iso_utc(vinculado),
                    rng.choice(["pin", "qr"]), _iso_utc(vinculado),
                    estado, bateria,
                    _iso_utc(datetime.combine(ultima, time(rng.randint(7, 22), 0))),
                    _iso_utc(datetime.combine(ultima, time(rng.randint(7, 22), 0))),
                    _iso_utc(plan["creado"]), _iso_utc(ultima),
                ),
            )
            device_id = cur.lastrowid
            plan["device_id"] = device_id
            self.dispositivos[uid] = {
                "id": device_id,
                "uid": plan["device_uid"],
                "vinculado": vinculado,
                "bateria": bateria,
                "estado": estado,
                "firmware": "1.4.2",
            }
            self.conn.execute(
                """
                INSERT INTO vinculacion_codigos
                    (dispositivo_id, metodo, codigo_hash, expira_en, usado_en,
                     usado_por_usuario_id, intentos, max_intentos, creado_en)
                VALUES (?, ?, ?, ?, ?, ?, 1, 5, ?)
                """,
                (
                    device_id, rng.choice(["pin", "qr"]), self._token_hex(),
                    _iso_utc(vinculado + timedelta(minutes=10)),
                    _iso_utc(vinculado), uid, _iso_utc(vinculado),
                ),
            )
            if rng.random() < 0.35:
                expirado = self.hoy - timedelta(days=rng.randint(1, 30))
                self.conn.execute(
                    """
                    INSERT INTO vinculacion_codigos
                        (dispositivo_id, metodo, codigo_hash, expira_en,
                         intentos, max_intentos, creado_en)
                    VALUES (?, 'pin', ?, ?, 0, 5, ?)
                    """,
                    (
                        device_id, self._token_hex(),
                        _iso_utc(datetime.combine(expirado, time(12, 0))),
                        _iso_utc(datetime.combine(expirado, time(11, 50))),
                    ),
                )

    def _token_hex(self) -> str:
        return "".join(f"{self.rng.getrandbits(8):02x}" for _ in range(32))

    def _asignar_transacciones(self) -> None:
        rng = self.rng
        cantidad = self.total_transacciones
        n = len(self.planes)
        minimo = max(3, min(10, cantidad // n))
        conteos = [minimo] * n
        restante = cantidad - sum(conteos)
        while restante < 0:
            for i in range(n):
                if conteos[i] > 1:
                    conteos[i] -= 1
                    restante += 1
                    break
            else:
                break
        pesos = [
            1.0 + rng.random() * 1.5
            + (1.2 if plan["idx"] == 0 else 0)
            + (0.5 if plan["device_uid"] else 0)
            for plan in self.planes
        ]
        for _ in range(restante):
            elegido = rng.choices(range(n), weights=pesos, k=1)[0]
            conteos[elegido] += 1
        for plan, conteo in zip(self.planes, conteos):
            plan["n_tx"] = conteo

    # ------------------------------------------------------------------
    # Movimientos, mensajes e IA
    # ------------------------------------------------------------------
    def _crear_movimientos(self, plan: dict) -> list[dict]:
        rng = self.rng
        uid = plan["uid"]
        catalogo = self.catalogo[uid]
        n = plan["n_tx"]
        factor = max(0.6, min(2.3, plan["ingreso_total"] / 2_000_000 or 1))

        tipos = ["gasto"] * max(1, n - 2) + ["ingreso", "ahorro"]
        while len(tipos) < n:
            tipos.append("gasto")
        for i in range(len(tipos)):
            if tipos[i] == "gasto" and rng.random() < 0.05:
                tipos[i] = "ingreso" if rng.random() < 0.45 else "ahorro"
        rng.shuffle(tipos)

        pesos_dia = [1.0 + (i / max(1, self.dias - 1)) * 1.4 for i in range(self.dias)]
        txs: list[dict] = []
        for i, tipo in enumerate(tipos):
            if i == 0:
                # Cada usuario tiene al menos un movimiento confirmado hoy,
                # para que el home y el simulador muestren datos del dia.
                fecha = self.hoy
            else:
                dia_idx = rng.choices(range(self.dias), weights=pesos_dia, k=1)[0]
                fecha = self.start + timedelta(days=dia_idx)
            dt = datetime.combine(fecha, time(rng.randint(7, 21), rng.randint(0, 59)))
            cuenta_id = self._cuenta_al_azar(catalogo)
            meta = None
            categoria_id = None
            if tipo == "ahorro":
                meta = rng.choice(self.metas[uid])
                meta_id = meta["id"]
                monto = _redondear(meta["aporte"] * rng.uniform(0.5, 2.2))
                monto = max(10000, min(monto, 600000))
                concepto = f"ahorro para {meta['nombre']}"
            else:
                lista = catalogo["gastos"] if tipo == "gasto" else catalogo["ingresos"]
                pesos = catalogo["pesos_gasto"] if tipo == "gasto" else catalogo["pesos_ingreso"]
                elegida = rng.choices(
                    [c["id"] for c in lista],
                    weights=[pesos[c["id"]] for c in lista],
                    k=1,
                )[0]
                categoria_id = elegida
                nombre = next(c["nombre"] for c in lista if c["id"] == elegida)
                opciones = CONCEPTOS.get(nombre, ("compra",))
                concepto = rng.choice(opciones)
                if tipo == "gasto":
                    base = BASES_GASTO.get(nombre, 15000)
                    monto = _redondear(base * factor * rng.uniform(0.35, 1.8))
                    if nombre in ("Vivienda y fijos", "Deudas", "Prestamos", "Préstamos"):
                        monto = _redondear(monto, 1000)
                else:
                    if nombre == "Trabajo":
                        base = max(plan["trabajo"], 250000)
                    elif nombre == "Apoyo familiar":
                        base = max(plan["apoyo"], 120000)
                    elif nombre == "Beca":
                        base = max(plan["beca"], 180000)
                    elif nombre == "Freelance":
                        base = max(plan["trabajo"] // 2, 150000)
                    else:
                        base = 180000
                    monto = _redondear(base * rng.uniform(0.6, 1.25), 1000)
                meta_id = None

            if plan["device_uid"]:
                origen = rng.choices(
                    ["dispositivo", "app_voz", "manual", "importacion"],
                    [0.45, 0.25, 0.25, 0.05],
                )[0]
            else:
                origen = rng.choices(
                    ["app_voz", "manual", "importacion"], [0.55, 0.40, 0.05]
                )[0]
            es_voz = origen in ("dispositivo", "app_voz")

            if i == 0:
                estado = "confirmado"
                is_deleted = False
            else:
                dias_atras = (self.hoy - fecha).days
                if origen in ("dispositivo", "app_voz", "manual") and dias_atras <= 14 and rng.random() < 0.22:
                    estado = "pendiente"
                else:
                    estado = "confirmado"
                is_deleted = estado == "confirmado" and rng.random() < 0.045

            if tipo == "gasto":
                texto = f"gaste {monto} en {concepto}"
            elif tipo == "ingreso":
                texto = f"recibi {monto} de {concepto}"
            else:
                texto = f"guarde {monto} para {meta['nombre']}"

            tx = {
                "tipo": tipo,
                "monto": monto,
                "categoria_id": categoria_id,
                "cuenta_id": cuenta_id,
                "meta_id": meta_id,
                "concepto": concepto[:255],
                "fecha_local": fecha.isoformat(),
                "fecha_hora": _iso_utc(dt),
                "dt": dt,
                "origen": origen,
                "texto": texto,
                "confianza": round(rng.uniform(0.62, 0.99), 3) if es_voz else None,
                "estado": estado,
                "is_deleted": is_deleted,
                "deleted_at": None,
                "eliminado_via": None,
                "device_uid": plan["device_uid"] or f"app-{uid}",
                "msg_key": f"m{i}" if es_voz else None,
            }
            if is_deleted:
                eliminado = dt + timedelta(hours=rng.randint(2, 72))
                limite = datetime.combine(self.hoy, time(23, 0)) - timedelta(hours=1)
                if eliminado > limite:
                    eliminado = limite
                if eliminado < dt + timedelta(minutes=5):
                    eliminado = dt + timedelta(minutes=5)
                tx["deleted_at"] = _iso_utc(eliminado)
                tx["eliminado_via"] = rng.choice(["app", "voz", "deshacer"])
            txs.append(tx)

        # Algunos mensajes agrupan dos movimientos del mismo dia.
        por_dia: dict[tuple, list[dict]] = {}
        for tx in txs:
            if tx["msg_key"]:
                por_dia.setdefault((tx["fecha_local"], tx["origen"]), []).append(tx)
        for grupo in por_dia.values():
            i = 0
            while i < len(grupo) - 1:
                if rng.random() < 0.12:
                    grupo[i + 1]["msg_key"] = grupo[i]["msg_key"]
                    i += 2
                else:
                    i += 1
        return txs

    def _insertar_movimientos(self, plan: dict) -> None:
        rng = self.rng
        uid = plan["uid"]
        txs = self._crear_movimientos(plan)
        self.txs[uid] = txs

        mensajes: dict[str, dict] = {}
        for tx in txs:
            clave = tx["msg_key"]
            if not clave:
                continue
            mensaje = mensajes.get(clave)
            if mensaje is None:
                mensaje = {
                    "key": clave,
                    "txs": [],
                    "textos": [],
                    "origen": tx["origen"],
                    "recibido": tx["dt"],
                    "confianzas": [],
                }
                mensajes[clave] = mensaje
            mensaje["txs"].append(tx)
            mensaje["textos"].append(tx["texto"])
            if tx["confianza"] is not None:
                mensaje["confianzas"].append(tx["confianza"])

        insertados = []
        for seq, mensaje in enumerate(sorted(mensajes.values(), key=lambda m: m["recibido"]), 1):
            txs_mensaje = mensaje["txs"]
            if any(t["estado"] == "pendiente" for t in txs_mensaje):
                estado = "procesado"
            elif all(t["is_deleted"] for t in txs_mensaje):
                estado = "descartado"
            else:
                estado = "confirmado"
            origen = mensaje["origen"]
            duracion = round(rng.uniform(1.0, 18.0), 1) if rng.random() < 0.75 else None
            confianza = max(mensaje["confianzas"]) if mensaje["confianzas"] else None
            texto = " y ".join(dict.fromkeys(mensaje["textos"]))[:500]
            recibido = mensaje["recibido"]
            procesado = recibido + timedelta(seconds=rng.randint(2, 18))
            cur = self.conn.execute(
                """
                INSERT INTO mensajes_dispositivo
                    (usuario_id, device_id, device_uid, message_id, texto_transcrito,
                     origen, duracion_audio_s, confianza_ia, estado, recibido_en,
                     procesado_en, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    uid, plan.get("device_id"), plan["device_uid"] or f"app-{uid}",
                    f"msg-{uid:03d}-{seq:04d}", texto, origen, duracion,
                    confianza, estado, _iso_utc(recibido), _iso_utc(procesado),
                ),
            )
            mensaje_id = cur.lastrowid
            for posicion, tx in enumerate(txs_mensaje, 1):
                cur_tx = self.conn.execute(
                    """
                    INSERT INTO transacciones
                        (usuario_id, mensaje_id, device_uid, secuencia, tipo, monto,
                         categoria_id, cuenta_id, meta_id, concepto, fecha_hora,
                         fecha_local, origen, texto_transcrito, confianza_ia,
                         estado, version, is_deleted, deleted_at, eliminado_via,
                         confirmado_en, creado_en, actualizado_en)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0,
                            NULL, NULL, ?, ?, ?)
                    """,
                    (
                        uid, mensaje_id, tx["device_uid"], posicion, tx["tipo"],
                        tx["monto"], tx["categoria_id"], tx["cuenta_id"], tx["meta_id"],
                        tx["concepto"], tx["fecha_hora"], tx["fecha_local"],
                        tx["origen"], tx["texto"], tx["confianza"], tx["estado"],
                        tx["fecha_hora"] if tx["estado"] == "confirmado" else None,
                        tx["fecha_hora"], tx["fecha_hora"],
                    ),
                )
                tx["id"] = cur_tx.lastrowid
                tx["mensaje_id"] = mensaje_id
            mensaje["id"] = mensaje_id
            mensaje["texto"] = texto
            mensaje["duracion"] = duracion
            mensaje["estado"] = estado
            mensaje["txs"] = txs_mensaje
            mensaje["confianza"] = confianza
            insertados.append(mensaje)

        # Movimientos sin mensaje (manuales o importados).
        for tx in txs:
            if tx["msg_key"]:
                continue
            cur_tx = self.conn.execute(
                """
                INSERT INTO transacciones
                    (usuario_id, mensaje_id, device_uid, secuencia, tipo, monto,
                     categoria_id, cuenta_id, meta_id, concepto, fecha_hora,
                     fecha_local, origen, texto_transcrito, confianza_ia,
                     estado, version, is_deleted, deleted_at, eliminado_via,
                     confirmado_en, creado_en, actualizado_en)
                VALUES (?, NULL, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL,
                        ?, 1, 0, NULL, NULL, ?, ?, ?)
                """,
                (
                    uid, tx["device_uid"], tx["tipo"], tx["monto"],
                    tx["categoria_id"], tx["cuenta_id"], tx["meta_id"],
                    tx["concepto"], tx["fecha_hora"], tx["fecha_local"],
                    tx["origen"], tx["estado"],
                    tx["fecha_hora"] if tx["estado"] == "confirmado" else None,
                    tx["fecha_hora"], tx["fecha_hora"],
                ),
            )
            tx["id"] = cur_tx.lastrowid

        # Borrado logico: se hace despues de insertar para que el disparador
        # de puntos se comporte como en la app real.
        for tx in txs:
            if tx["is_deleted"]:
                self.conn.execute(
                    """
                    UPDATE transacciones
                       SET is_deleted = 1, deleted_at = ?, eliminado_via = ?,
                           actualizado_en = ?
                     WHERE id = ?
                    """,
                    (tx["deleted_at"], tx["eliminado_via"], tx["deleted_at"], tx["id"]),
                )

        # Ediciones: el disparador guarda la version anterior.
        candidatas = [
            tx for tx in txs
            if tx["estado"] == "confirmado" and not tx["is_deleted"]
        ]
        rng.shuffle(candidatas)
        for tx in candidatas[: rng.randint(0, 2)]:
            nuevo = max(500, tx["monto"] - rng.choice([500, 1000, 2000]))
            self.conn.execute(
                "UPDATE transacciones SET monto = ?, actualizado_en = ? WHERE id = ?",
                (nuevo, _iso_utc(tx["dt"] + timedelta(hours=1)), tx["id"]),
            )
            tx["monto"] = nuevo

        # Intentos de voz que no produjeron texto.
        if plan["device_uid"] and rng.random() < 0.4:
            fecha = self.hoy - timedelta(days=rng.randint(1, 30))
            recibido = datetime.combine(fecha, time(rng.randint(8, 20), rng.randint(0, 59)))
            cur = self.conn.execute(
                """
                INSERT INTO mensajes_dispositivo
                    (usuario_id, device_id, device_uid, message_id, texto_transcrito,
                     origen, duracion_audio_s, confianza_ia, estado, recibido_en,
                     procesado_en, error)
                VALUES (?, ?, ?, ?, NULL, 'dispositivo', ?, NULL, 'recibido', ?, NULL,
                        'STT_SIN_TEXTO')
                """,
                (
                    uid, plan.get("device_id"), plan["device_uid"],
                    f"msg-{uid:03d}-voz-fallida", round(rng.uniform(1.0, 9.0), 1),
                    _iso_utc(recibido),
                ),
            )
            insertados.append({
                "id": cur.lastrowid,
                "texto": None,
                "duracion": round(rng.uniform(1.0, 9.0), 1),
                "estado": "recibido",
                "txs": [],
                "recibido": recibido,
                "confianza": None,
                "error": "STT_SIN_TEXTO",
                "key": f"fallido-{uid}",
            })

        self.mensajes[uid] = insertados

    def _crear_interacciones(self) -> None:
        rng = self.rng
        for uid, mensajes in self.mensajes.items():
            for mensaje in mensajes:
                recibido = mensaje["recibido"]
                if mensaje["duracion"] is not None:
                    if rng.random() < 0.7:
                        proveedor, modelo, tokens_in, tokens_out = (
                            "gemini", "gemini-2.5-flash",
                            rng.randint(40, 220), rng.randint(15, 90),
                        )
                    else:
                        proveedor, modelo, tokens_in, tokens_out = (
                            "faster-whisper", "small", None, None,
                        )
                    if mensaje.get("error"):
                        salida = {"error": mensaje["error"]}
                    else:
                        salida = {"texto": mensaje["texto"]}
                    self.conn.execute(
                        """
                        INSERT INTO interacciones_ia
                            (usuario_id, mensaje_id, proveedor, modelo, version_prompt,
                             entrada_json, salida_json, confianza, latencia_ms,
                             tokens_entrada, tokens_salida, creado_en)
                        VALUES (?, ?, ?, ?, 'transcribir-v1', ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            uid, mensaje["id"], proveedor, modelo,
                            _json({
                                "mime_type": "audio/wav",
                                "duracion_s": mensaje["duracion"],
                                "idioma": IDIOMA,
                            }),
                            _json(salida),
                            mensaje["confianza"],
                            rng.randint(320, 2400), tokens_in, tokens_out,
                            _iso_utc(recibido + timedelta(seconds=1)),
                        ),
                    )
                if mensaje["texto"]:
                    propuestas = [
                        {"tipo": tx["tipo"], "monto": tx["monto"]}
                        for tx in mensaje["txs"]
                    ]
                    self.conn.execute(
                        """
                        INSERT INTO interacciones_ia
                            (usuario_id, mensaje_id, proveedor, modelo, version_prompt,
                             entrada_json, salida_json, confianza, latencia_ms,
                             tokens_entrada, tokens_salida, creado_en)
                        VALUES (?, ?, 'ollama', 'qwen3:4b', 'interpretar-v1', ?, ?, ?,
                                ?, ?, ?, ?)
                        """,
                        (
                            uid, mensaje["id"],
                            _json({"texto": mensaje["texto"], "idioma": IDIOMA}),
                            _json({
                                "intent": "registrar",
                                "transacciones": propuestas[:3],
                            }),
                            mensaje["confianza"], rng.randint(250, 1900),
                            rng.randint(90, 380), rng.randint(20, 140),
                            _iso_utc(recibido + timedelta(seconds=4)),
                        ),
                    )

    # ------------------------------------------------------------------
    # Metas, puntos, cierres y salud
    # ------------------------------------------------------------------
    def _completar_metas_y_puntos(self) -> None:
        rng = self.rng
        for plan in self.planes:
            uid = plan["uid"]
            txs = self.txs[uid]
            ahorros = [
                tx for tx in txs
                if tx["tipo"] == "ahorro" and tx["estado"] == "confirmado" and not tx["is_deleted"]
            ]
            ahorrado: dict[int, int] = {}
            ultima_fecha: dict[int, str] = {}
            for tx in ahorros:
                ahorrado[tx["meta_id"]] = ahorrado.get(tx["meta_id"], 0) + tx["monto"]
                ultima_fecha[tx["meta_id"]] = tx["fecha_local"]
                self.conn.execute(
                    """
                    INSERT INTO metas_eventos
                        (usuario_id, meta_id, transaccion_id, tipo, periodo_clave,
                         puntos, salud_delta, detalle_json, creado_en)
                    VALUES (?, ?, ?, 'aporte', ?, 0, 0, ?, ?)
                    """,
                    (
                        uid, tx["meta_id"], tx["id"],
                        f"{tx['fecha_local']}-{tx['id']}",
                        _json({"monto": tx["monto"]}),
                        _iso_utc(tx["dt"] + timedelta(seconds=5)),
                    ),
                )

            for meta in self.metas[uid]:
                total = ahorrado.get(meta["id"], 0)
                completada = False
                if total >= 50000 and meta["monto"] <= total:
                    completada = True
                elif total >= 50000 and rng.random() < 0.45:
                    self.conn.execute(
                        "UPDATE metas SET monto_meta = ?, actualizado_en = ? WHERE id = ?",
                        (total, _iso_utc(datetime.now() - BOGOTA_UTC_OFFSET), meta["id"]),
                    )
                    meta["monto"] = total
                    completada = True
                if completada:
                    fecha = ultima_fecha.get(meta["id"], self.hoy.isoformat())
                    self.conn.execute(
                        """
                        UPDATE metas
                           SET estado = 'completada', completada_en = ?, actualizado_en = ?
                         WHERE id = ?
                        """,
                        (fecha + "T21:00:00Z", _iso_utc(datetime.now() - BOGOTA_UTC_OFFSET), meta["id"]),
                    )
                    meta["completada"] = True
                    self.conn.execute(
                        """
                        INSERT INTO metas_eventos
                            (usuario_id, meta_id, tipo, periodo_clave, puntos,
                             salud_delta, detalle_json, creado_en)
                        VALUES (?, ?, 'cumplida', ?, 10, 3, ?, ?)
                        """,
                        (
                            uid, meta["id"], fecha,
                            _json({"monto_meta": meta["monto"]}),
                            _iso_utc(datetime.fromisoformat(fecha + "T21:00:00")),
                        ),
                    )
                    self.conn.execute(
                        """
                        INSERT OR IGNORE INTO puntos_log
                            (usuario_id, meta_id, fecha_local, puntos, motivo,
                             clave_unica, detalle_json, otorgado_en)
                        VALUES (?, ?, ?, 10, 'meta_cumplida', ?, ?, ?)
                        """,
                        (
                            uid, meta["id"], fecha, f"meta-{meta['id']}",
                            _json({"meta": meta["nombre"]}),
                            _iso_utc(datetime.fromisoformat(fecha + "T21:00:05")),
                        ),
                    )
                    self.salud[uid] = min(100, self.salud[uid] + 3)
                else:
                    meta["completada"] = False
                    if rng.random() < 0.35:
                        clave = f"{self.hoy.year}-{self.hoy.month:02d}"
                        self.conn.execute(
                            """
                            INSERT OR IGNORE INTO metas_eventos
                                (usuario_id, meta_id, tipo, periodo_clave, puntos,
                                 salud_delta, detalle_json, creado_en)
                            VALUES (?, ?, 'recordatorio', ?, 0, 0, ?, ?)
                            """,
                            (
                                uid, meta["id"], clave,
                                _json({"ahorrado": total}),
                                _iso_utc(datetime.combine(
                                    self.hoy - timedelta(days=rng.randint(0, 10)),
                                    time(8, 0),
                                )),
                            ),
                        )
                    if total < meta["monto"] * 0.5 and rng.random() < 0.3:
                        clave = f"{self.hoy.year}-{self.hoy.month:02d}"
                        self.conn.execute(
                            """
                            INSERT OR IGNORE INTO metas_eventos
                                (usuario_id, meta_id, tipo, periodo_clave, puntos,
                                 salud_delta, detalle_json, creado_en)
                            VALUES (?, ?, 'atrasada', ?, 0, -2, ?, ?)
                            """,
                            (
                                uid, meta["id"], clave,
                                _json({"ahorrado": total, "meta": meta["monto"]}),
                                _iso_utc(datetime.combine(
                                    self.hoy - timedelta(days=rng.randint(0, 5)),
                                    time(9, 0),
                                )),
                            ),
                        )

            confirmadas = [
                tx for tx in txs
                if tx["estado"] == "confirmado" and not tx["is_deleted"]
            ]
            semanas: dict[tuple[int, int], list[str]] = {}
            for tx in confirmadas:
                anio, semana, _ = date.fromisoformat(tx["fecha_local"]).isocalendar()
                semanas.setdefault((anio, semana), []).append(tx["fecha_local"])
            for (anio, semana), fechas in semanas.items():
                if len(set(fechas)) < 3:
                    continue
                fecha = max(fechas)
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO puntos_log
                        (usuario_id, fecha_local, puntos, motivo, clave_unica,
                         detalle_json, otorgado_en)
                    VALUES (?, ?, 5, 'bonus_semana', ?, ?, ?)
                    """,
                    (
                        uid, fecha, f"semana-{anio}-W{semana:02d}",
                        _json({"dias_con_registro": len(set(fechas))}),
                        _iso_utc(datetime.fromisoformat(fecha + "T20:00:00")),
                    ),
                )

            for hito in (10, 25, 50, 100):
                if len(confirmadas) >= hito:
                    fecha = sorted(tx["fecha_local"] for tx in confirmadas)[hito - 1]
                    self.conn.execute(
                        """
                        INSERT OR IGNORE INTO puntos_log
                            (usuario_id, fecha_local, puntos, motivo, clave_unica,
                             detalle_json, otorgado_en)
                        VALUES (?, ?, 15, 'bonus_hito', ?, ?, ?)
                        """,
                        (
                            uid, fecha, f"hito-{hito}",
                            _json({"registros": hito}),
                            _iso_utc(datetime.fromisoformat(fecha + "T20:00:00")),
                        ),
                    )

    def _presupuesto_en(self, uid: int, dia: date) -> int:
        monto = 0
        for fecha, valor in self.historial[uid]:
            if fecha <= dia:
                monto = valor
            else:
                break
        return monto or self.planes[0]["presupuesto"]

    def _crear_cierres_y_salud(self) -> None:
        rng = self.rng
        for plan in self.planes:
            uid = plan["uid"]
            dias: dict[str, dict] = {}
            for tx in self.txs[uid]:
                if tx["estado"] != "confirmado" or tx["is_deleted"]:
                    continue
                fila = dias.setdefault(
                    tx["fecha_local"],
                    {"ingresos": 0, "gastos": 0, "ahorro": 0, "num": 0},
                )
                if tx["tipo"] == "ingreso":
                    fila["ingresos"] += tx["monto"]
                elif tx["tipo"] == "gasto":
                    fila["gastos"] += tx["monto"]
                else:
                    fila["ahorro"] += tx["monto"]
                fila["num"] += 1
            candidatos = sorted(d for d in dias if d < self.hoy.isoformat())
            if not candidatos:
                continue
            cuantos = min(len(candidatos), rng.randint(2, 7))
            elegidos = set(rng.sample(candidatos, cuantos))
            elegidos.add(candidatos[-1])

            for fecha_texto in sorted(elegidos):
                fecha = date.fromisoformat(fecha_texto)
                fila = dias[fecha_texto]
                presupuesto = self._presupuesto_en(uid, fecha)
                proporcion = fila["gastos"] / presupuesto if presupuesto else 0
                if fila["gastos"] == 0:
                    delta, calificacion = 0, "bien"
                elif proporcion <= 0.8:
                    delta, calificacion = 3, "bien"
                elif proporcion <= 1.0:
                    delta, calificacion = 1, "bien"
                elif proporcion <= 1.25:
                    delta, calificacion = -4, "regular"
                else:
                    delta, calificacion = -8, "mal"
                inicio = self.salud[uid]
                fin = max(0, min(100, inicio + delta))
                cerrado = datetime.combine(fecha, HORA_CIERRE)
                porcentaje = int(round(100 * proporcion))
                cur = self.conn.execute(
                    """
                    INSERT INTO cierres_dia
                        (usuario_id, fecha_local, total_ingresos, total_gastos,
                         total_ahorrado, balance_neto, presupuesto_diario,
                         porcentaje_usado, calificacion, num_registros,
                         salud_inicio, salud_fin, version, cerrado_en)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        uid, fecha_texto, fila["ingresos"], fila["gastos"],
                        fila["ahorro"], fila["ingresos"] - fila["gastos"],
                        presupuesto, max(0, porcentaje), calificacion,
                        fila["num"], inicio, fin, _iso_utc(cerrado),
                    ),
                )
                self.conn.execute(
                    """
                    INSERT INTO salud_log
                        (usuario_id, fecha_local, regla_codigo, motivo,
                         salud_anterior, salud_nueva, referencia_tipo,
                         referencia_id, detalle_json, creado_en)
                    VALUES (?, ?, ?, 'cierre_dia', ?, ?, 'cierre', ?, ?, ?)
                    """,
                    (
                        uid, fecha_texto, f"cierre_{calificacion}", inicio, fin,
                        cur.lastrowid,
                        _json({
                            "gastos": fila["gastos"],
                            "presupuesto": presupuesto,
                        }),
                        _iso_utc(cerrado + timedelta(minutes=1)),
                    ),
                )
                self.salud[uid] = fin

            ultima = date.fromisoformat(sorted(elegidos)[-1])
            self.conn.execute(
                """
                UPDATE estado_mascota
                   SET salud = ?, ultima_actualizacion = ?
                 WHERE usuario_id = ?
                """,
                (self.salud[uid], _iso_utc(datetime.combine(ultima, HORA_CIERRE)), uid),
            )

    def _actualizar_progreso(self) -> None:
        for plan in self.planes:
            uid = plan["uid"]
            fechas = sorted({
                tx["fecha_local"]
                for tx in self.txs[uid]
                if tx["estado"] == "confirmado" and not tx["is_deleted"]
            })
            total = len([
                tx for tx in self.txs[uid]
                if tx["estado"] == "confirmado" and not tx["is_deleted"]
            ])
            mejor = actual = 0
            for i, texto in enumerate(fechas):
                dia = date.fromisoformat(texto)
                if i == 0:
                    actual = 1
                else:
                    anterior = date.fromisoformat(fechas[i - 1])
                    actual = actual + 1 if (dia - anterior).days == 1 else 1
                mejor = max(mejor, actual)
            if fechas:
                ultima = date.fromisoformat(fechas[-1])
                if (self.hoy - ultima).days > 1:
                    actual = 0
            else:
                actual = 0
            etapa = 3 if total >= 60 else 2 if total >= 30 else 1 if total >= 10 else 0
            aprobada = None
            if etapa >= 1:
                aprobada = _iso_utc(datetime.combine(
                    date.fromisoformat(fechas[min(9, len(fechas) - 1)]), time(20, 0)
                ))
            self.conn.execute(
                """
                UPDATE progreso_etapa
                   SET etapa_actual = ?, racha_actual = ?, mejor_racha = ?,
                       etapa1_aprobada_en = ?, actualizado_en = ?
                 WHERE usuario_id = ?
                """,
                (
                    etapa, actual, max(mejor, actual), aprobada,
                    _iso_utc(datetime.combine(self.hoy, time(21, 0))), uid,
                ),
            )

    # ------------------------------------------------------------------
    # Alertas, notificaciones y dispositivo
    # ------------------------------------------------------------------
    def _crear_alertas(self) -> None:
        rng = self.rng

        def alerta(uid, tipo, severidad, titulo, mensaje, fecha_local, **extra):
            leida = rng.random() < 0.55
            leida_en = None
            if leida:
                leida_en = _iso_utc(datetime.combine(
                    fecha_local + timedelta(days=rng.randint(0, 1)),
                    time(rng.randint(18, 23), rng.randint(0, 59)),
                ))
            is_deleted = 1 if rng.random() < 0.04 else 0
            deleted_at = None
            if is_deleted:
                deleted_at = _iso_utc(datetime.combine(
                    fecha_local + timedelta(days=2), time(10, 0)
                ))
            self.conn.execute(
                """
                INSERT OR IGNORE INTO alertas_log
                    (usuario_id, tipo, severidad, titulo, mensaje, fecha_local,
                     transaccion_id, categoria_id, meta_id, dispositivo_id,
                     valor_actual, valor_limite, datos_json, leida, leida_en,
                     is_deleted, deleted_at, creado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uid, tipo, severidad, titulo, mensaje, fecha_local.isoformat(),
                    extra.get("transaccion_id"), extra.get("categoria_id"),
                    extra.get("meta_id"), extra.get("dispositivo_id"),
                    extra.get("valor_actual"), extra.get("valor_limite"),
                    _json(extra.get("datos")) if extra.get("datos") else None,
                    1 if leida else 0, leida_en, is_deleted, deleted_at,
                    _iso_utc(datetime.combine(fecha_local, time(rng.randint(6, 22), 0))),
                ),
            )

        for plan in self.planes:
            uid = plan["uid"]
            presupuesto = plan["presupuesto"]
            gastos_por_dia: dict[str, int] = {}
            for tx in self.txs[uid]:
                if tx["tipo"] != "gasto" or tx["estado"] != "confirmado" or tx["is_deleted"]:
                    continue
                gastos_por_dia[tx["fecha_local"]] = (
                    gastos_por_dia.get(tx["fecha_local"], 0) + tx["monto"]
                )
            for fecha_texto, gasto in gastos_por_dia.items():
                if gasto <= presupuesto:
                    continue
                alerta(
                    uid, "presupuesto_diario_excedido", "advertencia",
                    "Te pasaste del presupuesto del dia",
                    f"Gastaste {gasto} y tu presupuesto era {presupuesto}.",
                    date.fromisoformat(fecha_texto),
                    valor_actual=gasto, valor_limite=presupuesto,
                )

            presupuesto_info = self.presupuestos.get(uid)
            if presupuesto_info and presupuesto_info["aprobado"]:
                mensual: dict[tuple[str, int], int] = {}
                for tx in self.txs[uid]:
                    if tx["tipo"] != "gasto" or tx["estado"] != "confirmado" or tx["is_deleted"]:
                        continue
                    clave = (tx["fecha_local"][:7], tx["categoria_id"])
                    mensual[clave] = mensual.get(clave, 0) + tx["monto"]
                for (mes, categoria_id), gasto in mensual.items():
                    limite = presupuesto_info["categorias"].get(categoria_id)
                    if not limite or gasto <= limite:
                        continue
                    anio, numero = int(mes[:4]), int(mes[5:7])
                    ultimo = calendar.monthrange(anio, numero)[1]
                    fecha = min(date(anio, numero, ultimo), self.hoy - timedelta(days=1))
                    alerta(
                        uid, "presupuesto_categoria_excedido", "advertencia",
                        "Categoria por encima del limite",
                        f"Superaste el limite mensual de la categoria.",
                        fecha,
                        categoria_id=categoria_id,
                        valor_actual=gasto, valor_limite=limite,
                    )

            for meta in self.metas[uid]:
                if meta.get("completada"):
                    alerta(
                        uid, "meta_cumplida", "info",
                        "Meta cumplida",
                        f"Completaste la meta {meta['nombre']}.",
                        self.hoy - timedelta(days=rng.randint(0, 20)),
                        meta_id=meta["id"], valor_actual=meta["monto"],
                    )
                elif rng.random() < 0.2:
                    alerta(
                        uid, "meta_atrasada", "advertencia",
                        "Tu meta necesita un empujon",
                        f"La meta {meta['nombre']} va atrasada.",
                        self.hoy - timedelta(days=rng.randint(1, 15)),
                        meta_id=meta["id"],
                    )

            if self.salud[uid] <= 20:
                alerta(
                    uid, "salud_critica", "critica",
                    "Nancy necesita atencion",
                    "Tu mascota llego a un nivel critico de salud.",
                    self.hoy - timedelta(days=1),
                    valor_actual=self.salud[uid], valor_limite=100,
                )

            for tx in self.txs[uid]:
                if tx["estado"] == "pendiente" and rng.random() < 0.12:
                    alerta(
                        uid, "confirmar_entendimiento", "info",
                        "Falta confirmar un movimiento",
                        "Nancy entendio un movimiento y espera tu confirmacion.",
                        date.fromisoformat(tx["fecha_local"]),
                        transaccion_id=tx["id"],
                    )
                elif tx["is_deleted"] and rng.random() < 0.25:
                    alerta(
                        uid, "movimiento_eliminado", "info",
                        "Movimiento eliminado",
                        f"Se movio a la papelera: {tx['concepto']}.",
                        date.fromisoformat(tx["fecha_local"]),
                        transaccion_id=tx["id"],
                    )

            if rng.random() < 0.45:
                alerta(
                    uid, "recordatorio_diario", "info",
                    "Recuerda registrar tus gastos",
                    "Un minuto hoy te ahorra sustos manana.",
                    self.hoy - timedelta(days=1),
                )
            if rng.random() < 0.3:
                alerta(
                    uid, "resumen_semanal", "info",
                    "Resumen de la semana",
                    "Mira como te fue esta semana con Nancy.",
                    self.hoy - timedelta(days=2),
                )
            if plan["idx"] in (5, 17) or plan["idx"] % 9 == 0:
                alerta(
                    uid, "perfil_incompleto", "advertencia",
                    "Completa tu perfil",
                    "Con unas preguntas mas Nancy entiende mejor tus finanzas.",
                    self.hoy - timedelta(days=3),
                )
            dispositivo = self.dispositivos.get(uid)
            if dispositivo:
                if dispositivo["bateria"] <= 25:
                    alerta(
                        uid, "bateria_baja", "advertencia",
                        "Bateria baja en tu FinaGotchi",
                        "Conecta el dispositivo para que no pierda el hilo.",
                        self.hoy - timedelta(days=1),
                        dispositivo_id=dispositivo["id"],
                        valor_actual=dispositivo["bateria"], valor_limite=100,
                    )
                if dispositivo["estado"] != "conectado" and rng.random() < 0.5:
                    alerta(
                        uid, "dispositivo_desconectado", "advertencia",
                        "Tu FinaGotchi esta sin conexion",
                        "Los registros quedan guardados y se sincronizan despues.",
                        self.hoy - timedelta(days=1),
                        dispositivo_id=dispositivo["id"],
                    )
                if rng.random() < 0.4:
                    alerta(
                        uid, "dispositivo_vinculado", "info",
                        "Dispositivo vinculado",
                        "Tu FinaGotchi quedo vinculado a tu cuenta.",
                        dispositivo["vinculado"].date(),
                        dispositivo_id=dispositivo["id"],
                    )
            if rng.random() < 0.25:
                alerta(
                    uid, "sincronizacion", "info",
                    "Sincronizacion completada",
                    "Los registros pendientes ya llegaron a la nube.",
                    self.hoy - timedelta(days=rng.randint(0, 5)),
                    dispositivo_id=dispositivo["id"] if dispositivo else None,
                )
            if rng.random() < 0.2:
                alerta(
                    uid, "racha_en_riesgo", "advertencia",
                    "Tu racha esta en riesgo",
                    "Registra un movimiento hoy para no perderla.",
                    self.hoy - timedelta(days=1),
                )
            mensajes_multiples = [m for m in self.mensajes.get(uid, []) if len(m["txs"]) > 1]
            if mensajes_multiples and rng.random() < 0.6:
                mensaje = rng.choice(mensajes_multiples)
                alerta(
                    uid, "registros_agrupados", "info",
                    "Agrupamos tus registros",
                    "Varios movimientos de una misma frase quedaron juntos.",
                    mensaje["recibido"].date(),
                )

    def _crear_notificaciones_telemetria_comandos(self) -> None:
        rng = self.rng
        for plan in self.planes:
            dispositivo = self.dispositivos.get(plan["uid"])
            if not dispositivo:
                continue
            uid = plan["uid"]
            device_id = dispositivo["id"]
            mensajes = self.mensajes.get(uid, [])

            for mensaje in mensajes:
                if not mensaje["txs"] or rng.random() > 0.35:
                    continue
                estado = rng.choices(["pendiente", "entregada", "leida"], [0.25, 0.3, 0.45])[0]
                creado = mensaje["recibido"] + timedelta(seconds=5)
                entregado = (
                    creado + timedelta(minutes=rng.randint(1, 10))
                    if estado != "pendiente" else None
                )
                leido = (
                    entregado + timedelta(minutes=rng.randint(1, 120))
                    if estado == "leida" else None
                )
                tx = mensaje["txs"][0]
                self.conn.execute(
                    """
                    INSERT INTO dispositivos_notificaciones
                        (dispositivo_id, usuario_id, mensaje_id, transaccion_id, tipo,
                         titulo, mensaje, payload_json, estado, creado_en,
                         entregado_en, leido_en)
                    VALUES (?, ?, ?, ?, 'movimiento_registrado', ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device_id, uid, mensaje["id"], tx.get("id"),
                        "Movimiento registrado", tx["concepto"],
                        _json({"monto": tx["monto"], "tipo": tx["tipo"]}),
                        estado, _iso_utc(creado),
                        _iso_utc(entregado) if entregado else None,
                        _iso_utc(leido) if leido else None,
                    ),
                )
                if leido:
                    self.conn.execute(
                        "UPDATE dispositivos_notificaciones SET leido_en = ? WHERE id = last_insert_rowid()",
                        (_iso_utc(leido),),
                    )

            vinculado = dispositivo["vinculado"]
            self.conn.execute(
                """
                INSERT INTO dispositivos_notificaciones
                    (dispositivo_id, usuario_id, tipo, titulo, mensaje,
                     payload_json, estado, creado_en, entregado_en, leido_en)
                VALUES (?, ?, 'dispositivo_vinculado', 'FinaGotchi vinculado',
                        'Ya puedes hablarle a Nancy desde el dispositivo.',
                        ?, 'leida', ?, ?, ?)
                """,
                (
                    device_id, uid, _json({"device_uid": dispositivo["uid"]}),
                    _iso_utc(vinculado), _iso_utc(vinculado + timedelta(seconds=30)),
                    _iso_utc(vinculado + timedelta(minutes=2)),
                ),
            )
            if dispositivo["bateria"] <= 25:
                estado = rng.choice(["pendiente", "entregada"])
                creado = datetime.combine(self.hoy - timedelta(days=1), time(18, 0))
                self.conn.execute(
                    """
                    INSERT INTO dispositivos_notificaciones
                        (dispositivo_id, usuario_id, tipo, titulo, mensaje,
                         payload_json, estado, creado_en, entregado_en, leido_en)
                    VALUES (?, ?, 'bateria_baja', 'Bateria baja',
                            'Conecta tu FinaGotchi para cargarla.', ?, ?, ?, ?, NULL)
                    """,
                    (
                        device_id, uid, _json({"bateria": dispositivo["bateria"]}),
                        estado, _iso_utc(creado),
                        _iso_utc(creado + timedelta(minutes=3)) if estado == "entregada" else None,
                    ),
                )

            telemetrias = rng.randint(6, 14)
            for _ in range(telemetrias):
                fecha = self.start + timedelta(days=rng.randint(0, self.dias - 1))
                recibido = datetime.combine(fecha, time(rng.randint(6, 23), rng.randint(0, 59)))
                tipo = rng.choices(["latido", "evento", "confirmacion"], [0.6, 0.25, 0.15])[0]
                mensaje_ref = rng.choice(mensajes)["key"] if mensajes and rng.random() < 0.5 else None
                duracion = round(rng.uniform(1.0, 20.0), 1) if tipo == "evento" and rng.random() < 0.6 else None
                self.conn.execute(
                    """
                    INSERT INTO dispositivos_telemetria
                        (dispositivo_id, usuario_id, message_id, tipo, bateria,
                         estado, boton, audio_duracion_s, payload_json, recibido_en,
                         fecha_local)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device_id, uid, mensaje_ref, tipo,
                        max(1, min(100, dispositivo["bateria"] + rng.randint(-8, 8))),
                        "reposo", rng.choice([0, 0, 1]),
                        duracion,
                        _json({
                            "firmware": dispositivo["firmware"],
                            "senal_wifi": rng.randint(-85, -40),
                        }),
                        _iso_utc(recibido), fecha.isoformat(),
                    ),
                )

            for indice in range(rng.randint(1, 3)):
                tipo = rng.choice(
                    ["sincronizar", "desvincular", "reiniciar",
                     "actualizar_firmware", "silenciar"]
                )
                estado = rng.choices(
                    ["pendiente", "enviado", "confirmado", "error"],
                    [0.15, 0.2, 0.55, 0.1],
                )[0]
                creado = datetime.combine(
                    self.hoy - timedelta(days=rng.randint(0, 30)),
                    time(rng.randint(7, 21), rng.randint(0, 59)),
                )
                enviado = creado + timedelta(seconds=rng.randint(5, 90)) if estado != "pendiente" else None
                confirmado = (
                    enviado + timedelta(seconds=rng.randint(5, 120))
                    if estado == "confirmado" else None
                )
                self.conn.execute(
                    """
                    INSERT INTO dispositivos_comandos
                        (dispositivo_id, usuario_id, tipo, payload_json, estado,
                         idempotency_key, error, creado_en, enviado_en, confirmado_en)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device_id, uid, tipo,
                        _json({"device_uid": dispositivo["uid"]}), estado,
                        f"{dispositivo['uid']}-cmd-{indice + 1}",
                        "Sin respuesta del dispositivo" if estado == "error" else None,
                        _iso_utc(creado),
                        _iso_utc(enviado) if enviado else None,
                        _iso_utc(confirmado) if confirmado else None,
                    ),
                )

    # ------------------------------------------------------------------
    # Cuenta, consentimientos y seguridad
    # ------------------------------------------------------------------
    def _crear_cuenta_y_seguridad(self) -> None:
        rng = self.rng
        ahora = datetime.combine(self.hoy, time(20, 0))
        user_agents = (
            "FinaGotchi/1.4.2 (Android 14; Pixel 7)",
            "FinaGotchi/1.4.2 (Android 13; Samsung SM-A546E)",
            "FinaGotchi/1.4.2 (iOS 18; iPhone 13)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FinaGotchiWeb/1.0",
        )

        for idx, plan in enumerate(self.planes):
            uid = plan["uid"]
            creado = plan["creado"]

            for tipo in ("terminos", "privacidad"):
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO consentimientos
                        (usuario_id, tipo, version, aceptado, aceptado_en)
                    VALUES (?, ?, '2026-01', 1, ?)
                    """,
                    (uid, tipo, _iso_utc(creado + timedelta(minutes=rng.randint(1, 30)))),
                )
            self.conn.execute(
                """
                INSERT OR IGNORE INTO consentimientos
                    (usuario_id, tipo, version, aceptado, aceptado_en)
                VALUES (?, 'datos_estudio_anonimo', '2026-01', ?, ?)
                """,
                (
                    uid, 1 if rng.random() < 0.55 else 0,
                    _iso_utc(creado + timedelta(minutes=rng.randint(31, 90))),
                ),
            )

            # Sesiones de refresco: algunas activas, otras vencidas o revocadas.
            total_sesiones = rng.randint(1, 3)
            for posicion in range(total_sesiones):
                creada = ahora - timedelta(
                    days=rng.randint(1, 180), hours=rng.randint(0, 23)
                )
                expira = creada + timedelta(days=30)
                revocada = rng.random() < 0.15
                revocado_en = creada + timedelta(days=rng.randint(1, 20)) if revocada else None
                if posicion == 0 and not revocada and expira < ahora:
                    # La sesion mas reciente del usuario sigue vigente.
                    creada = ahora - timedelta(days=rng.randint(1, 20))
                    expira = creada + timedelta(days=30)
                self.conn.execute(
                    """
                    INSERT INTO sesiones_refresco
                        (usuario_id, token_hash, expira_en, revocado_en,
                         user_agent, ip, creado_en)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uid, self._token_hex(), _iso_utc(expira),
                        _iso_utc(revocado_en) if revocado_en else None,
                        rng.choice(user_agents),
                        f"192.168.{rng.randint(0, 255)}.{rng.randint(1, 254)}",
                        _iso_utc(creada),
                    ),
                )

            # Recuperacion de contrasena: usados, vencidos y vigentes.
            if idx % 3 == 0:
                for posicion in range(rng.randint(1, 2)):
                    creado_token = ahora - timedelta(
                        days=rng.randint(1, 60), hours=rng.randint(0, 23)
                    )
                    expira = creado_token + timedelta(hours=2)
                    usado = creado_token + timedelta(minutes=rng.randint(3, 90))
                    self.conn.execute(
                        """
                        INSERT INTO tokens_recuperacion
                            (usuario_id, token_hash, expira_en, usado_en, creado_en)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            uid, self._token_hex(), _iso_utc(expira),
                            _iso_utc(usado) if posicion == 0 else None,
                            _iso_utc(creado_token),
                        ),
                    )

            # Verificacion de correo: la mayoria ya la uso.
            if idx % 4 != 3:
                creado_token = creado + timedelta(minutes=rng.randint(2, 20))
                self.conn.execute(
                    """
                    INSERT INTO tokens_verificacion_correo
                        (usuario_id, token_hash, expira_en, usado_en, creado_en)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        uid, self._token_hex(),
                        _iso_utc(creado_token + timedelta(hours=24)),
                        _iso_utc(creado_token + timedelta(minutes=rng.randint(3, 90))),
                        _iso_utc(creado_token),
                    ),
                )
            if idx % 7 == 0:
                creado_token = ahora - timedelta(days=rng.randint(2, 30))
                self.conn.execute(
                    """
                    INSERT INTO tokens_verificacion_correo
                        (usuario_id, token_hash, expira_en, creado_en)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        uid, self._token_hex(),
                        _iso_utc(creado_token + timedelta(hours=24)),
                        _iso_utc(creado_token),
                    ),
                )

            # Retos educativos respondidos.
            if rng.random() < 0.65:
                retos = ["interes_compuesto", "inflacion", "diversificacion"]
                for codigo in rng.sample(retos, k=rng.randint(1, len(retos))):
                    respondido = ahora - timedelta(
                        days=rng.randint(1, 90), hours=rng.randint(0, 23)
                    )
                    self.conn.execute(
                        """
                        INSERT OR IGNORE INTO retos_respuestas
                            (usuario_id, reto_codigo, opcion_elegida,
                             es_correcta, respondido_en)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            uid, codigo, rng.choice("ABCD"),
                            1 if rng.random() < 0.6 else 0,
                            _iso_utc(respondido),
                        ),
                    )

        # Casos limite de eliminacion de cuenta.
        pendientes = [self.planes[i] for i in (7, 14) if i < len(self.planes)]
        for plan in pendientes:
            solicitada = datetime.combine(
                self.hoy - timedelta(days=rng.randint(1, 20)), time(10, 0)
            )
            ejecutar = solicitada + timedelta(days=30)
            self.conn.execute(
                """
                INSERT INTO solicitudes_eliminacion_cuenta
                    (usuario_id, solicitada_en, ejecutar_despues_de,
                     conservar_datos_anonimos, estado)
                VALUES (?, ?, ?, ?, 'pendiente')
                """,
                (
                    plan["uid"], _iso_utc(solicitada), _iso_utc(ejecutar),
                    1 if rng.random() < 0.5 else 0,
                ),
            )
            self.conn.execute(
                """
                UPDATE usuarios
                   SET estado = 'pendiente_eliminacion', actualizado_en = ?
                 WHERE id = ?
                """,
                (_iso_utc(solicitada), plan["uid"]),
            )
            self.conn.execute(
                """
                UPDATE sesiones_refresco
                   SET revocado_en = COALESCE(revocado_en, ?)
                 WHERE usuario_id = ?
                """,
                (_iso_utc(solicitada), plan["uid"]),
            )

        if len(self.planes) > 20:
            plan = self.planes[20]
            solicitada = datetime.combine(self.hoy - timedelta(days=60), time(9, 0))
            resuelta = solicitada + timedelta(days=4)
            self.conn.execute(
                """
                INSERT INTO solicitudes_eliminacion_cuenta
                    (usuario_id, solicitada_en, ejecutar_despues_de,
                     conservar_datos_anonimos, estado, resuelta_en)
                VALUES (?, ?, ?, 0, 'cancelada', ?)
                """,
                (
                    plan["uid"], _iso_utc(solicitada),
                    _iso_utc(solicitada + timedelta(days=30)), _iso_utc(resuelta),
                ),
            )

    # ------------------------------------------------------------------
    # Verificacion y resumen
    # ------------------------------------------------------------------
    def _verificar(self) -> None:
        fk = self.conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk:
            muestra = [tuple(fila) for fila in fk[:5]]
            raise RuntimeError(
                f"El dataset dejo {len(fk)} violaciones de clave foranea: {muestra}"
            )

        integridad = self.conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integridad != "ok":
            raise RuntimeError(f"integrity_check fallo: {integridad}")

        usuarios = self.conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        dispositivos = self.conn.execute("SELECT COUNT(*) FROM dispositivos").fetchone()[0]
        if usuarios != self.total_usuarios:
            raise RuntimeError(f"Se esperaban {self.total_usuarios} usuarios y hay {usuarios}")
        if dispositivos > usuarios:
            raise RuntimeError("Hay mas dispositivos que usuarios")
        if self.total_dispositivos and dispositivos != self.total_dispositivos:
            raise RuntimeError(
                f"Se esperaban {self.total_dispositivos} dispositivos y hay {dispositivos}"
            )
        repetidos = self.conn.execute(
            """
            SELECT usuario_id, COUNT(*) FROM dispositivos
             GROUP BY usuario_id HAVING COUNT(*) > 1
            """
        ).fetchall()
        if repetidos:
            raise RuntimeError(f"Usuarios con mas de un dispositivo: {repetidos}")

        total_tx = self.conn.execute("SELECT COUNT(*) FROM transacciones").fetchone()[0]
        if total_tx != self.total_transacciones:
            raise RuntimeError(
                f"Se esperaban {self.total_transacciones} transacciones y hay {total_tx}"
            )

        sin_puntos = self.conn.execute(
            """
            SELECT COUNT(*) FROM transacciones t
             WHERE t.estado = 'confirmado' AND t.is_deleted = 0
               AND NOT EXISTS (
                   SELECT 1 FROM puntos_log p
                    WHERE p.usuario_id = t.usuario_id
                      AND p.transaccion_id = t.id
                      AND p.motivo = 'registro_valido'
               )
            """
        ).fetchone()[0]
        if sin_puntos:
            raise RuntimeError(f"{sin_puntos} transacciones confirmadas sin puntos")

        vistas = [
            fila[0]
            for fila in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name"
            )
        ]
        if not vistas:
            raise RuntimeError("La base no tiene vistas: ejecuta database/init_db.py")
        for vista in vistas:
            self.conn.execute(f'SELECT * FROM "{vista}" LIMIT 1').fetchone()

        self.conn.commit()

    def resumen(self) -> dict:
        tablas = {}
        for (nombre,) in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ):
            tablas[nombre] = self.conn.execute(
                f'SELECT COUNT(*) FROM "{nombre}"'
            ).fetchone()[0]

        usuarios = self.conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        con_dispositivo = self.conn.execute(
            "SELECT COUNT(DISTINCT usuario_id) FROM dispositivos WHERE usuario_id IS NOT NULL"
        ).fetchone()[0]
        confirmadas = self.conn.execute(
            "SELECT COUNT(*) FROM transacciones WHERE estado = 'confirmado'"
        ).fetchone()[0]
        pendientes = self.conn.execute(
            "SELECT COUNT(*) FROM transacciones WHERE estado = 'pendiente'"
        ).fetchone()[0]
        eliminadas = self.conn.execute(
            "SELECT COUNT(*) FROM transacciones WHERE is_deleted = 1"
        ).fetchone()[0]
        rango = self.conn.execute(
            "SELECT MIN(fecha_local), MAX(fecha_local) FROM transacciones"
        ).fetchone()
        puntos = self.conn.execute("SELECT COALESCE(SUM(puntos), 0) FROM puntos_log").fetchone()[0]
        salud = self.conn.execute(
            "SELECT COALESCE(AVG(salud), 0) FROM estado_mascota"
        ).fetchone()[0]
        metas = self.conn.execute("SELECT COUNT(*) FROM metas").fetchone()[0]
        metas_cumplidas = self.conn.execute(
            "SELECT COUNT(*) FROM metas WHERE estado = 'completada'"
        ).fetchone()[0]
        vistas = self.conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'view'"
        ).fetchone()[0]

        return {
            "usuarios": usuarios,
            "usuarios_con_dispositivo": con_dispositivo,
            "usuarios_solo_app": usuarios - con_dispositivo,
            "dispositivos": tablas.get("dispositivos", 0),
            "transacciones": tablas.get("transacciones", 0),
            "transacciones_confirmadas": confirmadas,
            "transacciones_pendientes": pendientes,
            "transacciones_eliminadas": eliminadas,
            "mensajes_dispositivo": tablas.get("mensajes_dispositivo", 0),
            "interacciones_ia": tablas.get("interacciones_ia", 0),
            "metas": metas,
            "metas_cumplidas": metas_cumplidas,
            "puntos_total": int(puntos),
            "salud_promedio": round(float(salud), 2),
            "cierres_dia": tablas.get("cierres_dia", 0),
            "alertas_log": tablas.get("alertas_log", 0),
            "vistas": vistas,
            "rango_fechas": {
                "desde": rango[0], "hasta": rango[1],
            },
            "tablas": tablas,
        }


# ----------------------------------------------------------------------
# Exportacion
# ----------------------------------------------------------------------
def _tablas(conn) -> list[str]:
    return [
        fila[0]
        for fila in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def exportar_csv(db_path, resumen: dict, *, semilla: int, salida=None, hoy=None) -> dict:
    """Escribe un CSV por tabla, ``manifest.json`` y ``README.md``."""
    salida = Path(salida) if salida else ROOT / "datasets" / "dataset_bd"
    carpeta = salida / "csv"
    carpeta.mkdir(parents=True, exist_ok=True)
    for anterior in carpeta.glob("*.csv"):
        anterior.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    archivos = []
    try:
        for tabla in _tablas(conn):
            cursor = conn.execute(f'SELECT * FROM "{tabla}"')
            columnas = [descripcion[0] for descripcion in cursor.description]
            ruta = carpeta / f"{tabla}.csv"
            with ruta.open("w", encoding="utf-8", newline="") as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow(columnas)
                filas = 0
                for fila in cursor:
                    escritor.writerow(
                        ["" if valor is None else valor for valor in fila]
                    )
                    filas += 1
            contenido = ruta.read_bytes()
            archivos.append({
                "tabla": tabla,
                "archivo": f"csv/{tabla}.csv",
                "filas": filas,
                "bytes": len(contenido),
                "sha256": hashlib.sha256(contenido).hexdigest(),
            })
    finally:
        conn.close()

    manifest = {
        "generado_en": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "semilla": semilla,
        "hoy": (hoy or date.today()).isoformat(),
        "resumen": resumen,
        "total_archivos": len(archivos),
        "total_filas": sum(item["filas"] for item in archivos),
        "archivos": archivos,
    }
    (salida / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (salida / "README.md").write_text(_texto_readme(resumen, manifest), encoding="utf-8")
    return manifest


def _texto_readme(resumen: dict, manifest: dict) -> str:
    lineas = [
        "# Dataset de FinaGotchi",
        "",
        "Dataset sintetico y reproducible para probar la app, el simulador y la",
        "API de FinaGotchi. Se genera dentro de `finagotchi.db` y se exporta a CSV.",
        "",
        f"- Generado: {manifest['generado_en']}",
        f"- Semilla: `{manifest['semilla']}`",
        f"- Fecha de referencia: {manifest['hoy']}",
        f"- Rango de movimientos: {resumen['rango_fechas']['desde']} a "
        f"{resumen['rango_fechas']['hasta']}",
        "",
        "## Contenido",
        "",
        "| Recurso | Cantidad |",
        "| --- | ---: |",
        f"| Usuarios | {resumen['usuarios']} |",
        f"| Usuarios con dispositivo | {resumen['usuarios_con_dispositivo']} |",
        f"| Usuarios solo app | {resumen['usuarios_solo_app']} |",
        f"| Dispositivos | {resumen['dispositivos']} |",
        f"| Transacciones | {resumen['transacciones']} |",
        f"| Transacciones confirmadas | {resumen['transacciones_confirmadas']} |",
        f"| Transacciones pendientes | {resumen['transacciones_pendientes']} |",
        f"| Transacciones en papelera | {resumen['transacciones_eliminadas']} |",
        f"| Mensajes de dispositivo/app | {resumen['mensajes_dispositivo']} |",
        f"| Interacciones de IA | {resumen['interacciones_ia']} |",
        f"| Metas | {resumen['metas']} |",
        f"| Metas cumplidas | {resumen['metas_cumplidas']} |",
        f"| Puntos otorgados | {resumen['puntos_total']} |",
        f"| Cierres de dia | {resumen['cierres_dia']} |",
        f"| Alertas | {resumen['alertas_log']} |",
        f"| Vistas disponibles | {resumen['vistas']} |",
        "",
        "Cada usuario tiene como maximo un dispositivo y siempre hay menos",
        "dispositivos que usuarios. Los usuarios sin dispositivo representan",
        "cuentas que solo usan la app (por ejemplo, iPhone o navegador).",
        "",
        "## Cuentas demo",
        "",
        "| Correo | Contrasena | Rol |",
        "| --- | --- | --- |",
        "| `simulador@finagotchi.local` | `simulador123` | Cuenta del simulador de PC |",
        "| `demo01@finagotchi.local` ... `demo24@finagotchi.local` | `Demo1234` | Usuarios demo |",
        "",
        "Las 25 cuentas usan `America/Bogota`, moneda COP y correo ya verificado.",
        "",
        "## Casos limite incluidos",
        "",
        "- 2 solicitudes de eliminacion de cuenta pendientes (estado",
        "  `pendiente_eliminacion`).",
        "- 1 solicitud de eliminacion cancelada.",
        "- Transacciones pendientes de confirmacion y transacciones en papelera.",
        "- Movimientos agrupados en un mismo mensaje de voz.",
        "- Ediciones de movimientos con historial en `transacciones_versiones`.",
        "- Metas activas y completadas, con eventos y puntos.",
        "- Alertas leidas/no leidas y eliminadas logicamente.",
        "- Dispositivos con bateria baja, sin conexion y comandos en distintos estados.",
        "- Tokens de recuperacion usados/vencidos y sesiones revocadas.",
        "",
        "## Archivos",
        "",
        "`manifest.json` contiene el conteo, tamano y SHA-256 de cada CSV.",
        "`csv/` tiene un archivo por tabla, con encabezados y UTF-8 sin BOM.",
        "",
        "Los valores `NULL` se exportan como campo vacio. Las columnas generadas",
        "(`ingreso_total_mensual`, `delta_salud`, `delta`) son de solo lectura.",
        "",
        "## Exportacion consolidada",
        "",
        "`consolidado/dataset_completo.csv` reune todas las tablas en formato largo:",
        "`tabla;id_registro;usuario_id;fecha;columna_fecha;campo;valor`. Usa UTF-8",
        "con BOM y separador `;` para abrirlo en Excel, incluye las celdas vacias y",
        "tiene su propio `consolidado/manifest_consolidado.json` con SHA-256.",
        "",
        "```powershell",
        "py -3 tools/exportar_csv_consolidado.py",
        'py -3 tools/exportar_csv_consolidado.py --separador "," --sin-bom --omitir-vacios',
        "```",
        "",
        "## Regenerar",
        "",
        "```powershell",
        "py -3 tools/generar_dataset_bd.py",
        "py -3 tools/generar_dataset_bd.py --semilla 1234 --transacciones 200",
        "py -3 tools/generar_dataset_bd.py --db C:\\ruta\\copia.db --no-exportar",
        "```",
        "",
        "El generador respalda la base en `backups/` antes de borrar los datos",
        "existentes. Conserva `plantilla_*` y `schema_migrations`.",
        "",
    ]
    return "\n".join(lineas)


def _normalizar_esquema(conn) -> None:
    """Alinea bases creadas con versiones antiguas del esquema.

    Algunas copias de ``finagotchi.db`` tienen ``dispositivos.device_id`` en
    lugar de ``dispositivos.device_uid``. El backend y ``001_schema.sql`` usan
    ``device_uid``, asi que se renombra la columna sin perder datos.
    """
    columnas = {fila[1] for fila in conn.execute("PRAGMA table_info(dispositivos)")}
    if "device_uid" not in columnas and "device_id" in columnas:
        conn.execute("ALTER TABLE dispositivos RENAME COLUMN device_id TO device_uid")
        conn.commit()


# ----------------------------------------------------------------------
# Orquestacion
# ----------------------------------------------------------------------
def generar_dataset(
    db_path=ROOT / "finagotchi.db",
    *,
    usuarios=25,
    dispositivos=18,
    transacciones=500,
    dias=120,
    semilla=20261104,
    respaldar=True,
    exportar=True,
    salida=None,
    hoy=None,
):
    """Respalda, regenera y exporta el dataset. Devuelve (resumen, respaldo, manifest)."""
    db_path = Path(db_path)
    if dispositivos > usuarios:
        raise ValueError("No puede haber mas dispositivos que usuarios")
    if usuarios < 1 or transacciones < 1:
        raise ValueError("Se necesita al menos un usuario y una transaccion")
    if dias < 7:
        raise ValueError("El periodo debe ser de al menos 7 dias")

    respaldo = None
    if respaldar and db_path.exists():
        carpeta = ROOT / "backups"
        carpeta.mkdir(parents=True, exist_ok=True)
        sello = datetime.now().strftime("%Y%m%d-%H%M%S")
        respaldo = carpeta / f"finagotchi-antes-dataset-{sello}.db"
        shutil.copy2(db_path, respaldo)

    init_db.init_sqlite(db_path)
    conn = init_db.connect(db_path)
    try:
        _normalizar_esquema(conn)
        generador = Generador(
            conn,
            usuarios=usuarios,
            dispositivos=dispositivos,
            transacciones=transacciones,
            dias=dias,
            semilla=semilla,
            hoy=hoy,
        )
        resumen = generador.ejecutar()
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except sqlite3.OperationalError:
            pass
        conn.commit()
    finally:
        conn.close()

    manifest = None
    if exportar:
        manifest = exportar_csv(
            db_path, resumen, semilla=semilla, salida=salida, hoy=hoy
        )
    return resumen, respaldo, manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera el dataset demo de FinaGotchi dentro de finagotchi.db",
    )
    parser.add_argument(
        "--db", default=str(ROOT / "finagotchi.db"),
        help="Base de datos destino (por defecto finagotchi.db)",
    )
    parser.add_argument("--usuarios", type=int, default=25, help="Numero de usuarios")
    parser.add_argument(
        "--dispositivos", type=int, default=18,
        help="Dispositivos fisicos (nunca mas que usuarios)",
    )
    parser.add_argument(
        "--transacciones", type=int, default=500, help="Transacciones a generar",
    )
    parser.add_argument("--dias", type=int, default=120, help="Dias de historia")
    parser.add_argument(
        "--semilla", type=int, default=20261104, help="Semilla reproducible",
    )
    parser.add_argument(
        "--hoy", type=date.fromisoformat, default=None,
        help="Fecha de referencia YYYY-MM-DD (por defecto hoy)",
    )
    parser.add_argument(
        "--salida", default=None,
        help="Carpeta de exportacion (por defecto datasets/dataset_bd)",
    )
    parser.add_argument(
        "--sin-respaldo", action="store_true", help="No copiar la base a backups/",
    )
    parser.add_argument(
        "--no-exportar", action="store_true", help="No generar CSV ni manifest",
    )
    args = parser.parse_args(argv)

    if args.dispositivos > args.usuarios:
        parser.error("--dispositivos no puede ser mayor que --usuarios")

    try:
        resumen, respaldo, manifest = generar_dataset(
            args.db,
            usuarios=args.usuarios,
            dispositivos=args.dispositivos,
            transacciones=args.transacciones,
            dias=args.dias,
            semilla=args.semilla,
            respaldar=not args.sin_respaldo,
            exportar=not args.no_exportar,
            salida=args.salida,
            hoy=args.hoy,
        )
    except Exception as exc:  # noqa: BLE001 - se muestra el error al usuario
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if respaldo:
        print(f"Respaldo: {respaldo}")
    print(f"Base:     {Path(args.db).resolve()}")
    print(
        "Usuarios: {usuarios} ({usuarios_con_dispositivo} con dispositivo, "
        "{usuarios_solo_app} solo app)".format(**resumen)
    )
    print(
        "Dispositivos: {dispositivos} | Transacciones: {transacciones} "
        "({transacciones_confirmadas} confirmadas, {transacciones_pendientes} "
        "pendientes, {transacciones_eliminadas} en papelera)".format(**resumen)
    )
    print(
        "Mensajes: {mensajes_dispositivo} | Interacciones IA: {interacciones_ia} | "
        "Metas: {metas} ({metas_cumplidas} cumplidas)".format(**resumen)
    )
    print(
        "Puntos: {puntos_total} | Salud promedio: {salud_promedio} | "
        "Vistas: {vistas}".format(**resumen)
    )
    if manifest:
        print(
            f"Exportado: {manifest['total_archivos']} CSV, "
            f"{manifest['total_filas']} filas, manifest.json y README.md"
        )
    print("Credenciales: simulador@finagotchi.local / simulador123")
    print("              demo01@finagotchi.local ... demo24@finagotchi.local / Demo1234")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())





