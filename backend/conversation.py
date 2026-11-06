"""Agente conversacional de FinaGotchi.

El agente separa dos responsabilidades:

- ``backend/ai.py`` interpreta el lenguaje y devuelve intencion + entidades.
- Este modulo valida, recuerda el estado del dialogo, pregunta y ejecuta.

El estado vive en memoria y se identifica por ``(usuario_id, dispositivo)``.
No es fuente de verdad financiera: si el backend se reinicia solo se pierde el
borrador en curso. Los movimientos pendientes siguen en las tablas existentes.
"""

import math
import os
import threading
import time
from datetime import date as date_cls
from datetime import timedelta

from . import ai, nlp, services

TTL_SEGUNDOS = 30 * 60
MAX_HISTORIAL = 12

SESIONES = {}
_LOCK = threading.Lock()

ESTADO_INACTIVA = "inactiva"
ESTADO_CONFIRMANDO_MOVIMIENTO = "confirmando_movimiento"
ESTADO_RECOPILANDO_META = "recopilando_meta"
ESTADO_CONFIRMANDO_META = "confirmando_meta"

FRASES_CORRECCION = (
    "cambia",
    "cambiar",
    "corrige",
    "corregir",
    "no era",
    "mejor dicho",
    "en realidad",
    "actualiza",
    "modifica",
)

PALABRAS_CONFIRMACION = tuple(dict.fromkeys(nlp.CONFIRMAR_WORDS + ("listo",)))
PALABRAS_CANCELACION = nlp.CANCELAR_WORDS


# ---------------------------------------------------------------------------
# Estado en memoria
# ---------------------------------------------------------------------------
def _clave(usuario_id, dispositivo_uid):
    return (int(usuario_id), str(dispositivo_uid or "app"))


def _ahora():
    return time.time()


def limpiar_sesiones():
    """Borra todos los estados. Util para pruebas y para reinicios controlados."""
    with _LOCK:
        SESIONES.clear()


def obtener_estado(usuario_id, dispositivo_uid=None):
    clave = _clave(usuario_id, dispositivo_uid)
    with _LOCK:
        estado = SESIONES.get(clave)
        if estado is None:
            return {"estado": ESTADO_INACTIVA, "accion_pendiente": None, "borrador": None}
        if _ahora() - estado.get("actualizado", 0) > TTL_SEGUNDOS:
            SESIONES.pop(clave, None)
            return {"estado": ESTADO_INACTIVA, "accion_pendiente": None, "borrador": None}
        return dict(estado)


def guardar_estado(usuario_id, dispositivo_uid, estado):
    clave = _clave(usuario_id, dispositivo_uid)
    estado = dict(estado)
    estado["actualizado"] = _ahora()
    estado.setdefault("historial", [])
    with _LOCK:
        SESIONES[clave] = estado
    return estado


def borrar_estado(usuario_id, dispositivo_uid=None):
    with _LOCK:
        SESIONES.pop(_clave(usuario_id, dispositivo_uid), None)


def _recordar(estado, texto, respuesta):
    historial = list(estado.get("historial") or [])
    historial.append({"usuario": texto, "nancy": respuesta})
    estado["historial"] = historial[-MAX_HISTORIAL:]
    return estado


# ---------------------------------------------------------------------------
# Utilidades de respuesta
# ---------------------------------------------------------------------------
def _moneda(valor):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        numero = 0
    signo = "-" if numero < 0 else ""
    return f"{signo}${abs(numero):,}".replace(",", ".")


def _respuesta(
    mensaje,
    tipo_respuesta,
    estado,
    datos=None,
    requiere_confirmacion=False,
    payload=None,
    intent=None,
    dispositivo_uid=None,
    usuario_id=None,
    texto=None,
):
    base = dict(payload or {})
    base.update(
        {
            "mensaje_nancy": mensaje,
            "tipo_respuesta": tipo_respuesta,
            "estado_conversacion": estado.get("estado", ESTADO_INACTIVA),
            "datos": datos or {},
            "requiere_confirmacion": bool(requiere_confirmacion),
        }
    )
    if intent is not None:
        base["intent"] = intent
    if dispositivo_uid is not None:
        base["dispositivo_uid"] = dispositivo_uid
    if usuario_id is not None:
        base["usuario_id"] = usuario_id
    if texto is not None:
        base.setdefault("texto_transcrito", texto)
    return base


def _describir_movimiento(transaccion):
    tipo = str(transaccion.get("tipo") or "movimiento").upper()
    partes = [f"{tipo} de {_moneda(transaccion.get('monto'))}"]
    if transaccion.get("categoria"):
        partes.append(f"en {transaccion['categoria']}")
    if transaccion.get("meta"):
        partes.append(f"para la meta {transaccion['meta']}")
    if transaccion.get("cuenta"):
        partes.append(f"desde {transaccion['cuenta']}")
    return " ".join(partes)


# ---------------------------------------------------------------------------
# Interpretacion
# ---------------------------------------------------------------------------
def _contexto(conn, usuario_id, estado):
    return {
        "fecha": services.local_date(),
        "estado": estado.get("estado"),
        "accion_pendiente": estado.get("accion_pendiente"),
        "borrador": estado.get("borrador"),
        "metas": nlp.metas_usuario(conn, usuario_id),
        "cuentas": [
            {"id": row["id"], "nombre": row["nombre"]}
            for row in conn.execute(
                "SELECT id, nombre FROM cuentas WHERE usuario_id = ? ORDER BY id",
                (usuario_id,),
            )
        ],
        "categorias": [
            {"id": row["id"], "nombre": row["nombre"], "tipo": row["tipo"]}
            for row in conn.execute(
                "SELECT id, nombre, tipo FROM categorias "
                "WHERE usuario_id = ? AND activa = 1 ORDER BY id",
                (usuario_id,),
            )
        ],
    }


def _interpretar(conn, usuario_id, texto, estado):
    interpretacion = None
    if (os.environ.get("NLP_USAR_IA") or "auto").strip().lower() != "off":
        interpretacion = ai.interpretar_conversacion(
            texto, _contexto(conn, usuario_id, estado)
        )
    if interpretacion is None:
        interpretacion = nlp.detectar_intencion_conversacional(texto)
        interpretacion["proveedor"] = None
        interpretacion["origen"] = "reglas"
    else:
        interpretacion["origen"] = "ia"
    return interpretacion


def _es_confirmacion(texto):
    normalized = nlp.normalize(texto)
    if not normalized or len(normalized.split()) > 8:
        return False
    return any(nlp.word_in_text(palabra, normalized) for palabra in PALABRAS_CONFIRMACION)


def _es_cancelacion(texto):
    normalized = nlp.normalize(texto)
    if not normalized or len(normalized.split()) > 8:
        return False
    return any(nlp.word_in_text(palabra, normalized) for palabra in PALABRAS_CANCELACION)


def _es_correccion(texto):
    normalized = nlp.normalize(texto)
    return any(nlp.word_in_text(palabra, normalized) for palabra in FRASES_CORRECCION)


# ---------------------------------------------------------------------------
# Movimientos
# ---------------------------------------------------------------------------
def _propuesta_movimiento(conn, usuario_id, texto, interpretacion):
    entidades = interpretacion.get("entidades") or {}
    return nlp.construir_movimiento(
        conn,
        usuario_id,
        texto,
        tipo=entidades.get("tipo"),
        monto=entidades.get("monto"),
        categoria=entidades.get("categoria"),
        cuenta=entidades.get("cuenta"),
        meta=entidades.get("meta"),
        concepto=entidades.get("concepto"),
        proveedor=interpretacion.get("proveedor"),
        latencia_ms=interpretacion.get("latencia_ms"),
    )


def _registrar_movimiento(
    conn,
    usuario_id,
    texto,
    interpretacion,
    estado,
    dispositivo_uid,
    device_id,
    origen,
    audio_duration_s,
    message_id=None,
):
    resultado = _propuesta_movimiento(conn, usuario_id, texto, interpretacion)
    if resultado.get("intent") != "registrar" or not resultado.get("transacciones"):
        mensaje = resultado.get("error") or "No pude entender el movimiento."
        if resultado.get("meta_sugerida"):
            mensaje = (
                f"No encontré la meta \"{resultado['meta_sugerida']}\". "
                "Dime el nombre exacto de una de tus metas o crea una nueva."
            )
        return _respuesta(
            mensaje,
            "aclaracion",
            {**estado, "estado": ESTADO_INACTIVA},
            datos={"metas": nlp.metas_usuario(conn, usuario_id)},
            intent="requiere_aclaracion",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )

    payload = services.create_message(
        conn,
        usuario_id,
        texto,
        message_id=message_id,
        device_id=device_id,
        device_uid=dispositivo_uid,
        origen=origen,
        audio_duration_s=audio_duration_s,
        interpretacion=resultado,
    )
    transaccion = (payload.get("transacciones") or [{}])[0]
    nuevo_estado = {
        **estado,
        "estado": ESTADO_CONFIRMANDO_MOVIMIENTO,
        "accion_pendiente": {
            "tipo": "confirmar_mensaje",
            "message_id": payload.get("id"),
            "texto": texto,
            "resumen": _describir_movimiento(transaccion),
        },
        "borrador": None,
    }
    _recordar(nuevo_estado, texto, "confirmacion")
    guardar_estado(usuario_id, dispositivo_uid, nuevo_estado)
    mensaje = (
        f"Entendí un {_describir_movimiento(transaccion)}. "
        "¿Está correcto? Puedes decir sí, está bien, ok, o corregirlo."
    )
    return _respuesta(
        mensaje,
        "confirmacion",
        nuevo_estado,
        datos={"transaccion": transaccion},
        requiere_confirmacion=True,
        payload=payload,
        intent="registrar",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _confirmar(conn, usuario_id, texto, estado, dispositivo_uid):
    accion = estado.get("accion_pendiente") or {}
    if accion.get("tipo") == "crear_meta":
        return _confirmar_meta(conn, usuario_id, texto, estado, dispositivo_uid)
    if accion.get("tipo") == "confirmar_mensaje" and accion.get("message_id"):
        payload = services.confirm_message(conn, usuario_id, accion["message_id"])
        borrar_estado(usuario_id, dispositivo_uid)
        if payload is None:
            return _respuesta(
                "No encontré el movimiento pendiente. Puedes dictarlo otra vez.",
                "error",
                {**estado, "estado": ESTADO_INACTIVA, "accion_pendiente": None},
                intent="requiere_aclaracion",
                dispositivo_uid=dispositivo_uid,
                usuario_id=usuario_id,
                texto=texto,
            )
        return _respuesta(
            f"Listo. Guardé {accion.get('resumen', 'el movimiento')}.",
            "resultado",
            {"estado": ESTADO_INACTIVA, "accion_pendiente": None, "borrador": None},
            datos={"puntos_otorgados": payload.get("puntos_otorgados", 0)},
            payload=payload,
            intent="registrar",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )
    return _respuesta(
        "No hay nada pendiente por confirmar.",
        "aclaracion",
        {**estado, "estado": ESTADO_INACTIVA, "accion_pendiente": None},
        intent="confirmar",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _cancelar(conn, usuario_id, texto, estado, dispositivo_uid):
    accion = estado.get("accion_pendiente") or {}
    if accion.get("tipo") == "confirmar_mensaje" and accion.get("message_id"):
        services.discard_message(conn, usuario_id, accion["message_id"])
    borrar_estado(usuario_id, dispositivo_uid)
    return _respuesta(
        "Entendido, lo descarté. No guardé ningún cambio.",
        "resultado",
        {"estado": ESTADO_INACTIVA, "accion_pendiente": None, "borrador": None},
        intent="cancelar",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _corregir_movimiento(conn, usuario_id, texto, interpretacion, estado, dispositivo_uid):
    accion = estado.get("accion_pendiente") or {}
    message_id = accion.get("message_id")
    if not message_id:
        return None
    payload = services.message_payload(conn, usuario_id, message_id)
    if not payload or not payload.get("transacciones"):
        return None
    actual = payload["transacciones"][0]
    entidades = interpretacion.get("entidades") or {}
    cambios = {}
    monto = nlp.parse_amount(nlp.normalize(texto))
    if monto is not None:
        cambios["monto"] = monto
    if entidades.get("categoria"):
        categoria = nlp.coincide_en_catalogo(
            entidades["categoria"],
            [
                {"id": row["id"], "nombre": row["nombre"]}
                for row in conn.execute(
                    "SELECT id, nombre FROM categorias WHERE usuario_id = ? AND activa = 1",
                    (usuario_id,),
                )
            ],
        )
        if categoria:
            cambios["categoria_id"] = categoria["id"]
    if entidades.get("meta") or entidades.get("cuenta"):
        pass
    if not cambios:
        return _respuesta(
            "¿Qué dato quieres corregir: el monto, la categoría, la cuenta o la meta?",
            "aclaracion",
            estado,
            intent="corregir",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )
    services.update_transaction(conn, usuario_id, actual["id"], cambios)
    payload = services.message_payload(conn, usuario_id, message_id)
    transaccion = payload["transacciones"][0]
    nuevo_estado = {
        **estado,
        "estado": ESTADO_CONFIRMANDO_MOVIMIENTO,
        "accion_pendiente": {
            "tipo": "confirmar_mensaje",
            "message_id": message_id,
            "texto": texto,
            "resumen": _describir_movimiento(transaccion),
        },
    }
    guardar_estado(usuario_id, dispositivo_uid, nuevo_estado)
    return _respuesta(
        f"Corregido: {_describir_movimiento(transaccion)}. ¿Está correcto ahora?",
        "confirmacion",
        nuevo_estado,
        datos={"transaccion": transaccion},
        requiere_confirmacion=True,
        payload=payload,
        intent="registrar",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


# ---------------------------------------------------------------------------
# Consultas simples
# ---------------------------------------------------------------------------
def _consulta_balance(conn, usuario_id, periodo, estado, dispositivo_uid, texto):
    periodo = periodo if periodo in ("hoy", "semana", "mes") else "hoy"
    hoy = services.local_date()
    if periodo == "hoy":
        resumen = services.metrics_daily(conn, usuario_id, hoy)
        resumen = {
            "desde": hoy,
            "hasta": hoy,
            "total_ingresos": resumen.get("total_ingresos", 0),
            "total_gastos": resumen.get("total_gastos", 0),
            "total_ahorrado": resumen.get("total_ahorrado", 0),
            "balance_neto": resumen.get("balance_neto", 0),
            "cupo_restante": resumen.get("cupo_restante"),
            "presupuesto_diario": resumen.get("presupuesto_diario"),
            "num_registros": resumen.get("num_registros", 0),
        }
        mensaje = (
            f"Hoy llevas {_moneda(resumen['total_gastos'])} en gastos y "
            f"{_moneda(resumen['total_ahorrado'])} en ahorro. "
            f"Tu balance neto es {_moneda(resumen['balance_neto'])}."
        )
        if resumen.get("cupo_restante") is not None:
            mensaje += f" Te queda un cupo diario de {_moneda(resumen['cupo_restante'])}."
    else:
        if periodo == "semana":
            desde = (date_cls.fromisoformat(hoy) - timedelta(days=6)).isoformat()
            etiqueta = "esta semana"
        else:
            desde = hoy[:7] + "-01"
            etiqueta = "este mes"
        totales = services.period_totals(conn, usuario_id, desde, hoy)
        resumen = {
            "desde": desde,
            "hasta": hoy,
            "total_ingresos": totales["ingresos"],
            "total_gastos": totales["gastos"],
            "total_ahorrado": totales["ahorro"],
            "balance_neto": totales["balance_neto"],
            "num_registros": totales["num_registros"],
        }
        mensaje = (
            f"En {etiqueta} registraste {_moneda(resumen['total_gastos'])} en gastos, "
            f"{_moneda(resumen['total_ingresos'])} en ingresos y "
            f"{_moneda(resumen['total_ahorrado'])} en ahorro. "
            f"El balance es {_moneda(resumen['balance_neto'])}."
        )
    estado = {**estado, "estado": ESTADO_INACTIVA, "accion_pendiente": None}
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos={"periodo": periodo, "resumen": resumen},
        intent="consulta_estado",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _consulta_metas(conn, usuario_id, estado, dispositivo_uid, texto):
    filas = conn.execute(
        "SELECT * FROM v_metas_estado WHERE usuario_id = ? ORDER BY fecha_limite, meta_id",
        (usuario_id,),
    ).fetchall()
    metas = [dict(row) for row in filas]
    if not metas:
        mensaje = "Todavía no tienes metas. Puedes decir: quiero crear una meta para comprar audífonos."
    else:
        partes = []
        for meta in metas[:5]:
            partes.append(
                f"{meta['nombre']}: llevas {_moneda(meta.get('ahorrado'))} de "
                f"{_moneda(meta.get('monto_meta'))}"
            )
        mensaje = "Tus metas van así. " + "; ".join(partes) + "."
    return _respuesta(
        mensaje,
        "consulta",
        {**estado, "estado": ESTADO_INACTIVA, "accion_pendiente": None},
        datos={"metas": metas},
        intent="consultar_metas",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _consulta_plan(conn, usuario_id, estado, dispositivo_uid, texto):
    plan = services.plan_resumen(conn, usuario_id)
    capacidad = plan.get("capacidad_mes_actual", 0)
    metas = plan.get("metas") or []
    if metas:
        detalle = "; ".join(
            f"{meta['nombre']} con {_moneda(meta.get('asignacion_mes_actual'))} al mes"
            for meta in metas[:5]
        )
        mensaje = (
            f"Este mes puedes ahorrar hasta {_moneda(capacidad)}. "
            f"El plan recomienda: {detalle}."
        )
    else:
        mensaje = f"Este mes puedes ahorrar hasta {_moneda(capacidad)} y no tienes metas activas."
    return _respuesta(
        mensaje,
        "consulta",
        {**estado, "estado": ESTADO_INACTIVA, "accion_pendiente": None},
        datos=plan,
        intent="consultar_plan",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _consulta_cuentas(conn, usuario_id, estado, dispositivo_uid, texto):
    cuentas = services.accounts_summary(conn, usuario_id)
    if cuentas:
        detalle = "; ".join(
            f"{cuenta['nombre']}: {_moneda(cuenta.get('saldo_actual'))}"
            for cuenta in cuentas[:6]
        )
        mensaje = f"Tus cuentas son: {detalle}."
    else:
        mensaje = "No tienes cuentas registradas."
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos={"cuentas": cuentas},
        intent="consultar_cuentas",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _consulta_categorias(conn, usuario_id, estado, dispositivo_uid, texto):
    categorias = services.categories_summary(conn, usuario_id)
    nombres = ", ".join(categoria["nombre"] for categoria in categorias[:10])
    mensaje = f"Tus categorías son: {nombres}." if nombres else "No tienes categorías."
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos={"categorias": categorias},
        intent="consultar_categorias",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _consulta_movimientos(conn, usuario_id, estado, dispositivo_uid, texto):
    movimientos = services.recent_transactions(conn, usuario_id, limit=8)
    if movimientos:
        detalle = "; ".join(
            f"{movimiento['tipo']} de {_moneda(movimiento['monto'])}"
            + (f" en {movimiento['categoria']}" if movimiento.get("categoria") else "")
            for movimiento in movimientos[:6]
        )
        mensaje = f"Tus últimos movimientos: {detalle}."
    else:
        mensaje = "Todavía no tienes movimientos registrados."
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos={"movimientos": movimientos},
        intent="consultar_movimientos",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _consulta_presupuesto(conn, usuario_id, estado, dispositivo_uid, texto):
    hoy = services.local_date()
    presupuesto = services.budget_for_day(conn, usuario_id, hoy)
    gastos = services.day_totals(conn, usuario_id, hoy)["gastos"]
    mensaje = (
        f"Tu presupuesto diario es {_moneda(presupuesto)}. "
        f"Hoy has gastado {_moneda(gastos)} y te quedan {_moneda(presupuesto - gastos)}."
    )
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos={
            "presupuesto_diario": presupuesto,
            "gastos_hoy": gastos,
            "cupo_restante": presupuesto - gastos,
        },
        intent="consultar_presupuesto",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _consulta_perfil(conn, usuario_id, estado, dispositivo_uid, texto):
    perfil = services.profile_summary(conn, usuario_id)
    usuario = perfil.get("usuario") or {}
    datos = perfil.get("perfil") or {}
    mensaje = (
        f"Tu perfil es {usuario.get('nombre', 'sin nombre')}. "
        f"Tu ingreso mensual declarado es {_moneda(datos.get('ingreso_total_mensual'))}."
    )
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos=perfil,
        intent="consultar_perfil",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


# ---------------------------------------------------------------------------
# Creacion de metas por dialogo
# ---------------------------------------------------------------------------
CAMPOS_META = {
    "nombre": "¿Para qué quieres crear la meta?",
    "monto_meta": "¿Cuánto cuesta aproximadamente?",
    "fecha_limite": "¿En cuánto tiempo quieres lograrlo? Por ejemplo, en cinco meses.",
    "frecuencia_ahorro": "¿Quieres aportar diaria, semanal, quincenal o mensualmente?",
    "prioridad": "¿Qué prioridad tiene frente a tus otras metas: alta, media o baja?",
}


def _nombre_limpio(texto):
    limpio = nlp.normalize(texto)
    limpio = re.sub(
        r"\b(quiero|quisiera|necesito|crear|crea|plantear|plantea|una|un|la|el|"
        r"meta|objetivo|para|de|del|comprar|comprarme|ahorrar|por|favor)\b",
        " ",
        limpio,
    )
    return re.sub(r"\s+", " ", limpio).strip(" .,;")[:30]


def _borrador_inicial(texto, entidades):
    entidades = entidades or {}
    borrador = {
        "nombre": entidades.get("nombre") or nlp.nombre_meta_probable(texto),
        "monto_meta": nlp._entero(entidades.get("monto")) or nlp.parse_amount(texto),
        "fecha_limite": None,
        "plazo_meses": nlp._entero(entidades.get("plazo_meses")),
        "plazo_dias": nlp._entero(entidades.get("plazo_dias")),
        "frecuencia_ahorro": entidades.get("frecuencia")
        or nlp.parse_frecuencia(texto),
        "prioridad": nlp._entero(entidades.get("prioridad"))
        or nlp.detect_priority(texto),
    }
    plazo = nlp.parse_plazo(texto)
    if plazo and not borrador["fecha_limite"]:
        borrador["fecha_limite"] = plazo["fecha_limite"]
        borrador["plazo_meses"] = plazo["meses"]
        borrador["plazo_dias"] = plazo["dias"]
    return borrador


def _actualizar_borrador(borrador, texto, entidades, campo_pendiente=None, forzar=False):
    borrador = dict(borrador or {})
    entidades = entidades or {}
    if entidades.get("nombre") and (forzar or not borrador.get("nombre")):
        borrador["nombre"] = str(entidades["nombre"])[:30]
    if campo_pendiente == "nombre" and not borrador.get("nombre"):
        borrador["nombre"] = _nombre_limpio(texto)

    monto = nlp._entero(entidades.get("monto"))
    if monto is None and (forzar or not borrador.get("monto_meta")):
        monto = nlp.parse_amount(texto)
    if monto and (forzar or not borrador.get("monto_meta")):
        borrador["monto_meta"] = monto

    if forzar or not borrador.get("fecha_limite"):
        plazo = nlp.parse_plazo(texto)
        if plazo is None and (entidades.get("plazo_meses") or entidades.get("plazo_dias")):
            plazo = nlp._plazo_resultado(
                entidades.get("plazo_meses") or 0, entidades.get("plazo_dias") or 0
            )
        if plazo:
            borrador["fecha_limite"] = plazo["fecha_limite"]
            borrador["plazo_meses"] = plazo["meses"]
            borrador["plazo_dias"] = plazo["dias"]

    frecuencia = entidades.get("frecuencia") or nlp.parse_frecuencia(texto)
    if frecuencia and (forzar or not borrador.get("frecuencia_ahorro")):
        borrador["frecuencia_ahorro"] = frecuencia

    prioridad = nlp._entero(entidades.get("prioridad")) or nlp.detect_priority(texto)
    if prioridad and (forzar or not borrador.get("prioridad")):
        borrador["prioridad"] = prioridad

    if borrador.get("nombre"):
        borrador["nombre"] = str(borrador["nombre"])[:30]
    return borrador


def _campo_faltante(borrador):
    for campo in ("nombre", "monto_meta", "fecha_limite", "frecuencia_ahorro", "prioridad"):
        if not borrador.get(campo):
            return campo
    return None


def _periodos_hasta(desde, hasta, frecuencia):
    dias = max(0, (hasta - desde).days)
    if frecuencia == "diaria":
        return max(1, dias)
    if frecuencia == "semanal":
        return max(1, dias // 7)
    if frecuencia == "quincenal":
        return max(1, dias // 15)
    meses = (hasta.year - desde.year) * 12 + (hasta.month - desde.month)
    if hasta.day >= desde.day:
        meses += 1
    return max(1, meses)


def _completar_borrador(borrador):
    """Calcula fecha, aporte y prioridad con Python, nunca con el LLM."""
    borrador = dict(borrador)
    if not borrador.get("prioridad"):
        borrador["prioridad"] = 3
    if not borrador.get("frecuencia_ahorro"):
        borrador["frecuencia_ahorro"] = "mensual"
    if not borrador.get("fecha_limite"):
        plazo = nlp._plazo_resultado(
            borrador.get("plazo_meses") or 6, borrador.get("plazo_dias") or 0
        )
        borrador["fecha_limite"] = plazo["fecha_limite"]
    inicio = date_cls.fromisoformat(services.local_date())
    limite = services.parse_date(borrador["fecha_limite"])
    if limite is None or limite <= inicio:
        limite = date_cls.fromisoformat(
            nlp._plazo_resultado(6, 0, inicio)["fecha_limite"]
        )
        borrador["fecha_limite"] = limite.isoformat()
    periodos = _periodos_hasta(inicio, limite, borrador["frecuencia_ahorro"])
    borrador["aporte_periodico"] = max(
        1, math.ceil(int(borrador["monto_meta"]) / periodos)
    )
    borrador["periodos"] = periodos
    return borrador


def _proponer_meta(conn, usuario_id, borrador, estado, dispositivo_uid, texto):
    borrador = _completar_borrador(borrador)
    simulacion = services.simulate_goal_draft(conn, usuario_id, borrador)
    detalle = simulacion.get("meta") or {}
    asignacion = (detalle.get("asignacion_mensual") or [0])[0]
    mensaje = (
        f"Voy a crear la meta {borrador['nombre']} por {_moneda(borrador['monto_meta'])}, "
        f"con fecha límite {borrador['fecha_limite']}, frecuencia "
        f"{borrador['frecuencia_ahorro']} y un aporte de "
        f"{_moneda(borrador['aporte_periodico'])} por periodo."
    )
    if detalle:
        mensaje += (
            f" El plan recomienda asignarle {_moneda(asignacion)} al mes "
            f"y su cumplimiento estimado es {round(float(detalle.get('cumplimiento') or 0) * 100)} %."
        )
    mensaje += " ¿La creo?"
    nuevo_estado = {
        **estado,
        "estado": ESTADO_CONFIRMANDO_META,
        "accion_pendiente": {"tipo": "crear_meta"},
        "borrador": borrador,
        "campo_pendiente": None,
    }
    _recordar(nuevo_estado, texto, mensaje)
    guardar_estado(usuario_id, dispositivo_uid, nuevo_estado)
    return _respuesta(
        mensaje,
        "confirmacion",
        nuevo_estado,
        datos={"borrador": borrador, "simulacion": simulacion},
        requiere_confirmacion=True,
        intent="crear_meta",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _recopilar_meta(
    conn,
    usuario_id,
    texto,
    entidades,
    estado,
    dispositivo_uid,
    forzar=False,
    intent="actualizar_meta",
):
    borrador = _actualizar_borrador(
        estado.get("borrador") or {},
        texto,
        entidades,
        campo_pendiente=estado.get("campo_pendiente"),
        forzar=forzar,
    )
    campo = _campo_faltante(borrador)
    if campo:
        nuevo_estado = {
            **estado,
            "estado": ESTADO_RECOPILANDO_META,
            "accion_pendiente": None,
            "borrador": borrador,
            "campo_pendiente": campo,
        }
        guardar_estado(usuario_id, dispositivo_uid, nuevo_estado)
        return _respuesta(
            CAMPOS_META[campo],
            "aclaracion",
            nuevo_estado,
            datos={"borrador": borrador, "campo_pendiente": campo},
            intent=intent,
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )
    return _proponer_meta(conn, usuario_id, borrador, estado, dispositivo_uid, texto)


def _confirmar_meta(conn, usuario_id, texto, estado, dispositivo_uid):
    borrador = estado.get("borrador") or {}
    try:
        meta = services.create_goal(conn, usuario_id, borrador)
    except services.ErrorMeta as exc:
        return _respuesta(
            f"No pude crear la meta: {exc.mensaje}",
            "error",
            estado,
            intent="crear_meta",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )
    borrar_estado(usuario_id, dispositivo_uid)
    return _respuesta(
        f"Listo. Creé la meta {meta.get('nombre')} por {_moneda(meta.get('monto_meta'))}.",
        "resultado",
        {"estado": ESTADO_INACTIVA, "accion_pendiente": None, "borrador": None},
        datos={"meta": meta},
        intent="crear_meta",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


def _ayuda(estado, dispositivo_uid, texto, usuario_id):
    mensaje = (
        "Puedes decirme: gasté 20 mil en almuerzo; ahorré 50 mil para mi meta; "
        "quiero crear una meta para comprar audífonos; ¿cómo me fue hoy?; "
        "balance de esta semana; ¿cómo van mis metas?; o cierra el día."
    )
    return _respuesta(
        mensaje,
        "ayuda",
        estado,
        intent="ayuda",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
def procesar_turno(
    conn,
    usuario_id,
    texto,
    device_id=None,
    dispositivo_uid=None,
    dispositivo=None,
    origen="app_voz",
    audio_duration_s=None,
    device_uid=None,
    message_id=None,
):
    """Procesa un turno de voz o texto y devuelve la respuesta de Nancy.

    ``dispositivo`` y ``dispositivo_uid`` son alias del mismo dato; se aceptan
    ambos para no romper a los llamadores existentes.
    """
    dispositivo_uid = dispositivo_uid or dispositivo or device_uid
    texto = (texto or "").strip()
    estado = obtener_estado(usuario_id, dispositivo_uid)

    if message_id:
        existente = services.message_por_message_id(conn, usuario_id, message_id)
        if existente is not None:
            existente["duplicado"] = True
            existente.setdefault("puntos_otorgados", 0)
            existente.setdefault("mensaje_nancy", "Ese mensaje ya lo había procesado.")
            existente.setdefault("tipo_respuesta", "resultado")
            existente.setdefault("estado_conversacion", estado.get("estado"))
            existente.setdefault("datos", {})
            existente.setdefault(
                "requiere_confirmacion", bool(existente.get("requiere_confirmacion"))
            )
            return existente

    if not texto:
        return _respuesta(
            "No recibí ninguna frase. Intenta hablar de nuevo.",
            "error",
            estado,
            intent="requiere_aclaracion",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto="",
        )

    interpretacion = _interpretar(conn, usuario_id, texto, estado)
    intent = interpretacion.get("intent") or "desconocido"

    accion = estado.get("accion_pendiente") or {}
    if accion:
        if _es_confirmacion(texto) or intent == "confirmar":
            return _confirmar(conn, usuario_id, texto, estado, dispositivo_uid)
        if _es_cancelacion(texto) or intent == "cancelar":
            return _cancelar(conn, usuario_id, texto, estado, dispositivo_uid)
        if accion.get("tipo") == "confirmar_mensaje" and (
            intent == "corregir" or _es_correccion(texto)
        ):
            corregido = _corregir_movimiento(
                conn, usuario_id, texto, interpretacion, estado, dispositivo_uid
            )
            if corregido is not None:
                return corregido
        if accion.get("tipo") == "crear_meta" and (
            intent == "corregir"
            or intent == "actualizar_meta"
            or _es_correccion(texto)
        ):
            return _recopilar_meta(
                conn,
                usuario_id,
                texto,
                interpretacion.get("entidades") or {},
                estado,
                dispositivo_uid,
                forzar=True,
            )

    if estado.get("estado") == ESTADO_RECOPILANDO_META or intent in (
        "crear_meta",
        "actualizar_meta",
    ):
        if intent == "crear_meta" and not estado.get("borrador"):
            return _recopilar_meta(
                conn,
                usuario_id,
                texto,
                interpretacion.get("entidades") or {},
                {**estado, "borrador": _borrador_inicial(texto, interpretacion.get("entidades"))},
                dispositivo_uid,
                intent="crear_meta",
            )
        return _recopilar_meta(
            conn,
            usuario_id,
            texto,
            interpretacion.get("entidades") or {},
            estado,
            dispositivo_uid,
        )

    if intent in ("registrar_movimiento", "registrar"):
        return _registrar_movimiento(
            conn,
            usuario_id,
            texto,
            interpretacion,
            estado,
            dispositivo_uid,
            device_id,
            origen,
            audio_duration_s,
            message_id=message_id,
        )
    if intent in ("confirmar", "cancelar"):
        return _respuesta(
            "No hay nada pendiente. Puedes dictarme un movimiento o pedirme un balance.",
            "aclaracion",
            estado,
            intent=intent,
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )
    if intent == "consultar_balance":
        periodo = (interpretacion.get("entidades") or {}).get("periodo") or "hoy"
        return _consulta_balance(
            conn, usuario_id, periodo, estado, dispositivo_uid, texto
        )
    if intent == "consultar_metas":
        return _consulta_metas(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_plan":
        return _consulta_plan(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_cuentas":
        return _consulta_cuentas(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_categorias":
        return _consulta_categorias(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_movimientos":
        return _consulta_movimientos(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_presupuesto":
        return _consulta_presupuesto(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_perfil":
        return _consulta_perfil(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "ayuda":
        return _ayuda(estado, dispositivo_uid, texto, usuario_id)
    if intent == "cerrar_dia":
        try:
            cierre = services.close_day(conn, usuario_id, services.local_date())
        except ValueError as exc:
            return _respuesta(
                f"No pude cerrar el día: {exc}",
                "error",
                estado,
                intent="cerrar_dia",
                dispositivo_uid=dispositivo_uid,
                usuario_id=usuario_id,
                texto=texto,
            )
        borrar_estado(usuario_id, dispositivo_uid)
        return _respuesta(
            "Listo, cerré el día. Ya puedes descansar.",
            "resultado",
            {"estado": ESTADO_INACTIVA, "accion_pendiente": None, "borrador": None},
            datos={"cierre": cierre},
            intent="cerrar_dia",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )

    return _respuesta(
        "No entendí esa frase. Puedes decirme qué gastaste, cuánto ahorraste, "
        "cómo va tu día o pedir ayuda.",
        "error",
        estado,
        intent="requiere_aclaracion",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
    )
