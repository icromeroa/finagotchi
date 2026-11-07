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
import re
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
ESTADO_CONFIRMANDO_ACCION = "confirmando_accion"

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


def invalidar_accion_pendiente(usuario_id, message_id):
    """Limpia el estado pendiente si se resuelve fuera del agente.

    La confirmacion humana se ejecuta desde distintas rutas: por voz, por texto
    y por los endpoints ``/messages/<id>/confirm`` y ``/discard``. Si el
    mensaje quedara confirmado pero el estado conversacional siguiera con el
    borrador, la siguiente frase se interpretaria como una respuesta a una
    accion que ya no existe. Esta funcion busca y borra esas sesiones, sin
    importar el dispositivo que confirme.
    """
    borradas = 0
    with _LOCK:
        for clave, estado in list(SESIONES.items()):
            if clave[0] != int(usuario_id):
                continue
            accion = (estado or {}).get("accion_pendiente") or {}
            if (
                accion.get("tipo") == "confirmar_mensaje"
                and str(accion.get("message_id")) == str(message_id)
            ):
                SESIONES.pop(clave, None)
                borradas += 1
    return borradas


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


MESES_HABLADOS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def _monto_hablado(valor):
    """Devuelve un monto natural para TTS, sin símbolos ni separadores.

    ``20000`` se convierte en ``20 mil pesos`` y ``1500000`` en
    ``un millón 500 mil pesos``. Así Piper no lee «veinte punto cero cero
    cero» ni deja escapar el símbolo de pesos.
    """
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        numero = 0
    if numero == 0:
        return "cero pesos"
    signo = "menos " if numero < 0 else ""
    numero = abs(numero)
    if numero >= 1_000_000:
        millones, resto = divmod(numero, 1_000_000)
        parte = "un millón" if millones == 1 else f"{millones} millones"
        if resto == 0:
            return f"{signo}{parte} de pesos"
        miles, resto = divmod(resto, 1000)
        if miles:
            parte += f" {miles} mil"
        if resto:
            parte += f" {resto}"
        return f"{signo}{parte} pesos"
    if numero >= 1000:
        miles, resto = divmod(numero, 1000)
        parte = "mil" if miles == 1 else f"{miles} mil"
        if resto:
            parte += f" {resto}"
        return f"{signo}{parte} pesos"
    return f"{signo}{numero} pesos"


def _texto_para_voz(mensaje):
    """Limpia un mensaje de pantalla para que sea pronunciable."""
    texto = str(mensaje or "")
    texto = texto.replace("$", "")
    # Quita los puntos de miles: 20.000 -> 20000.
    texto = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", texto)
    for palabra in ("GASTO", "INGRESO", "AHORRO"):
        texto = texto.replace(palabra, palabra.lower())
    return re.sub(r"\s+", " ", texto).strip()


def _fecha_hablada(valor):
    """Convierte una fecha ISO en una frase natural para TTS."""
    try:
        fecha = date_cls.fromisoformat(str(valor))
    except (TypeError, ValueError):
        return str(valor or "")
    return f"{fecha.day} de {MESES_HABLADOS[fecha.month - 1]} de {fecha.year}"


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
    texto_voz=None,
):
    base = dict(payload or {})
    base.update(
        {
            "mensaje_nancy": mensaje,
            "texto_voz": texto_voz or _texto_para_voz(mensaje),
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
    tipo = str(transaccion.get("tipo") or "movimiento").lower()
    partes = [f"un {tipo} de {_moneda(transaccion.get('monto'))}"]
    if transaccion.get("categoria"):
        partes.append(f"en {transaccion['categoria']}")
    if transaccion.get("meta"):
        partes.append(f"para la meta {transaccion['meta']}")
    if transaccion.get("cuenta"):
        partes.append(f"desde {transaccion['cuenta']}")
    return " ".join(partes)


def _describir_movimiento_hablado(transaccion):
    """Resumen corto y natural del movimiento para la voz."""
    tipo = str(transaccion.get("tipo") or "movimiento").lower()
    partes = [f"un {tipo} de {_monto_hablado(transaccion.get('monto'))}"]
    if transaccion.get("categoria"):
        partes.append(f"en {str(transaccion['categoria']).lower()}")
    if transaccion.get("meta"):
        partes.append(f"para la meta {transaccion['meta']}")
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
    respaldo = nlp.detectar_intencion_conversacional(texto)
    interpretacion = None
    if (os.environ.get("NLP_USAR_IA") or "auto").strip().lower() != "off":
        interpretacion = ai.interpretar_conversacion(
            texto, _contexto(conn, usuario_id, estado)
        )
    if interpretacion is None:
        interpretacion = respaldo
        interpretacion["proveedor"] = None
        interpretacion["origen"] = "reglas"
        return interpretacion

    interpretacion["origen"] = "ia"
    entidades = dict(interpretacion.get("entidades") or {})
    respaldo_entidades = respaldo.get("entidades") or {}
    # El LLM interpreta, pero las reglas cubren sus dudas y nunca dejan que
    # una respuesta vacia convierta una frase clara en un error.
    if interpretacion.get("intent") == "desconocido" and respaldo.get("intent") != "desconocido":
        interpretacion["intent"] = respaldo["intent"]
        interpretacion["motivo_reglas"] = "el modelo no clasifico la frase"
    for clave, valor in respaldo_entidades.items():
        if entidades.get(clave) in (None, "", []):
            entidades[clave] = valor
    interpretacion["entidades"] = entidades
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
            "resumen_hablado": _describir_movimiento_hablado(transaccion),
        },
        "borrador": None,
    }
    _recordar(nuevo_estado, texto, "confirmacion")
    guardar_estado(usuario_id, dispositivo_uid, nuevo_estado)
    mensaje = (
        f"¿Registro {_describir_movimiento(transaccion)}? "
        "Puedes decir sí, está bien, ok, o corregirlo."
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
        texto_voz=f"¿Registro {_describir_movimiento_hablado(transaccion)}?",
    )


def _confirmar(conn, usuario_id, texto, estado, dispositivo_uid):
    accion = estado.get("accion_pendiente") or {}
    if accion.get("tipo") == "crear_meta":
        return _confirmar_meta(conn, usuario_id, texto, estado, dispositivo_uid)
    if accion.get("tipo") in (
        "eliminar_movimiento",
        "editar_movimiento",
        "crear_cuenta",
        "crear_categoria",
        "actualizar_presupuesto",
        "actualizar_perfil",
        "eliminar_meta",
    ):
        return _confirmar_accion(conn, usuario_id, texto, estado, dispositivo_uid)
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
            texto_voz=(
                f"Listo. Guardé "
                f"{accion.get('resumen_hablado') or 'el movimiento'}."
            ),
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
            "resumen_hablado": _describir_movimiento_hablado(transaccion),
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
        texto_voz=(
            "Corregido. "
            f"¿Registro {_describir_movimiento_hablado(transaccion)}?"
        ),
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
        texto_voz = (
            f"Hoy llevas {_monto_hablado(resumen['total_gastos'])} en gastos y "
            f"{_monto_hablado(resumen['total_ahorrado'])} en ahorro. "
            f"Tu balance neto es {_monto_hablado(resumen['balance_neto'])}."
        )
        if resumen.get("cupo_restante") is not None:
            mensaje += f" Te queda un cupo diario de {_moneda(resumen['cupo_restante'])}."
            texto_voz += (
                f" Te queda un cupo diario de "
                f"{_monto_hablado(resumen['cupo_restante'])}."
            )
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
        texto_voz = (
            f"En {etiqueta} registraste "
            f"{_monto_hablado(resumen['total_gastos'])} en gastos, "
            f"{_monto_hablado(resumen['total_ingresos'])} en ingresos y "
            f"{_monto_hablado(resumen['total_ahorrado'])} en ahorro. "
            f"El balance es {_monto_hablado(resumen['balance_neto'])}."
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
        texto_voz=texto_voz,
    )


def _consulta_metas(conn, usuario_id, estado, dispositivo_uid, texto):
    filas = conn.execute(
        "SELECT * FROM v_metas_estado WHERE usuario_id = ? ORDER BY fecha_limite, meta_id",
        (usuario_id,),
    ).fetchall()
    metas = [dict(row) for row in filas]
    if not metas:
        mensaje = "Todavía no tienes metas. Puedes decir: quiero crear una meta para comprar audífonos."
        texto_voz = mensaje
    else:
        partes = []
        partes_voz = []
        for meta in metas[:5]:
            partes.append(
                f"{meta['nombre']}: llevas {_moneda(meta.get('ahorrado'))} de "
                f"{_moneda(meta.get('monto_meta'))}"
            )
            partes_voz.append(
                f"{meta['nombre']}: llevas {_monto_hablado(meta.get('ahorrado'))} de "
                f"{_monto_hablado(meta.get('monto_meta'))}"
            )
        mensaje = "Tus metas van así. " + "; ".join(partes) + "."
        texto_voz = "Tus metas van así. " + "; ".join(partes_voz) + "."
    return _respuesta(
        mensaje,
        "consulta",
        {**estado, "estado": ESTADO_INACTIVA, "accion_pendiente": None},
        datos={"metas": metas},
        intent="consultar_metas",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
        texto_voz=texto_voz,
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
        texto_voz = (
            f"Este mes puedes ahorrar hasta {_monto_hablado(capacidad)}. "
            f"El plan ya tiene asignación para {len(metas)} meta"
            + ("" if len(metas) == 1 else "s")
            + "."
        )
    else:
        mensaje = f"Este mes puedes ahorrar hasta {_moneda(capacidad)} y no tienes metas activas."
        texto_voz = (
            f"Este mes puedes ahorrar hasta {_monto_hablado(capacidad)} "
            "y no tienes metas activas."
        )
    return _respuesta(
        mensaje,
        "consulta",
        {**estado, "estado": ESTADO_INACTIVA, "accion_pendiente": None},
        datos=plan,
        intent="consultar_plan",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
        texto_voz=texto_voz,
    )


def _consulta_cuentas(conn, usuario_id, estado, dispositivo_uid, texto):
    cuentas = services.accounts_summary(conn, usuario_id)
    if cuentas:
        detalle = "; ".join(
            f"{cuenta['nombre']}: {_moneda(cuenta.get('saldo_actual'))}"
            for cuenta in cuentas[:6]
        )
        detalle_voz = "; ".join(
            f"{cuenta['nombre']}: {_monto_hablado(cuenta.get('saldo_actual'))}"
            for cuenta in cuentas[:6]
        )
        mensaje = f"Tus cuentas son: {detalle}."
        texto_voz = f"Tus cuentas son: {detalle_voz}."
    else:
        mensaje = "No tienes cuentas registradas."
        texto_voz = mensaje
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos={"cuentas": cuentas},
        intent="consultar_cuentas",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
        texto_voz=texto_voz,
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
        texto_voz=mensaje,
    )


def _consulta_movimientos(conn, usuario_id, estado, dispositivo_uid, texto):
    movimientos = services.recent_transactions(conn, usuario_id, limit=8)
    if movimientos:
        detalle = "; ".join(
            f"{movimiento['tipo']} de {_moneda(movimiento['monto'])}"
            + (f" en {movimiento['categoria']}" if movimiento.get("categoria") else "")
            for movimiento in movimientos[:6]
        )
        detalle_voz = "; ".join(
            f"{movimiento['tipo']} de {_monto_hablado(movimiento['monto'])}"
            + (f" en {movimiento['categoria']}" if movimiento.get("categoria") else "")
            for movimiento in movimientos[:4]
        )
        mensaje = f"Tus últimos movimientos: {detalle}."
        texto_voz = f"Tus últimos movimientos: {detalle_voz}."
    else:
        mensaje = "Todavía no tienes movimientos registrados."
        texto_voz = mensaje
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos={"movimientos": movimientos},
        intent="consultar_movimientos",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
        texto_voz=texto_voz,
    )


def _consulta_presupuesto(conn, usuario_id, estado, dispositivo_uid, texto):
    hoy = services.local_date()
    presupuesto = services.budget_for_day(conn, usuario_id, hoy)
    gastos = services.day_totals(conn, usuario_id, hoy)["gastos"]
    mensaje = (
        f"Tu presupuesto diario es {_moneda(presupuesto)}. "
        f"Hoy has gastado {_moneda(gastos)} y te quedan {_moneda(presupuesto - gastos)}."
    )
    texto_voz = (
        f"Tu presupuesto diario es {_monto_hablado(presupuesto)}. "
        f"Hoy has gastado {_monto_hablado(gastos)} y te quedan "
        f"{_monto_hablado(presupuesto - gastos)}."
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
        texto_voz=texto_voz,
    )


def _consulta_perfil(conn, usuario_id, estado, dispositivo_uid, texto):
    perfil = services.profile_summary(conn, usuario_id)
    usuario = perfil.get("usuario") or {}
    datos = perfil.get("perfil") or {}
    mensaje = (
        f"Tu perfil es {usuario.get('nombre', 'sin nombre')}. "
        f"Tu ingreso mensual declarado es {_moneda(datos.get('ingreso_total_mensual'))}."
    )
    texto_voz = (
        f"Tu perfil es {usuario.get('nombre', 'sin nombre')}. "
        f"Tu ingreso mensual declarado es "
        f"{_monto_hablado(datos.get('ingreso_total_mensual'))}."
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
        texto_voz=texto_voz,
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
    diagnostico = simulacion.get("diagnostico") or {}
    if detalle:
        if asignacion > 0:
            mensaje += (
                f" El plan recomienda asignarle {_moneda(asignacion)} al mes "
                f"y su cumplimiento estimado es {round(float(detalle.get('cumplimiento') or 0) * 100)} %."
            )
        else:
            motivo = diagnostico.get("mensaje") or "no hay capacidad libre en el plan"
            mensaje += (
                f" El plan todavía no puede asignarle nada a esta meta: {motivo} "
                "Puedo crearla, pero no puedo prometerte que se cumpla con tu capacidad actual."
            )
    mensaje += " ¿La creo?"
    texto_voz = (
        f"Voy a crear la meta {borrador['nombre']} por "
        f"{_monto_hablado(borrador['monto_meta'])}, con fecha límite "
        f"{_fecha_hablada(borrador['fecha_limite'])} y un aporte de "
        f"{_monto_hablado(borrador['aporte_periodico'])} por periodo."
    )
    if detalle and asignacion > 0:
        texto_voz += (
            f" El plan recomienda asignarle {_monto_hablado(asignacion)} al mes."
        )
    elif detalle:
        texto_voz += " El plan todavía no puede asignarle capacidad."
    texto_voz += " ¿La creo?"
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
        texto_voz=texto_voz,
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
        texto_voz=(
            f"Listo. Creé la meta {meta.get('nombre')} por "
            f"{_monto_hablado(meta.get('monto_meta'))}."
        ),
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


def _movimiento_objetivo(conn, usuario_id, texto, entidades):
    movimientos = services.recent_transactions(conn, usuario_id, limit=20)
    if not movimientos:
        return None
    monto = nlp._entero((entidades or {}).get("monto")) or nlp.parse_amount(texto)
    if monto:
        for movimiento in movimientos:
            if int(movimiento.get("monto") or 0) == monto:
                return movimiento
    return movimientos[0]


def _nombre_dicho(texto, palabra):
    normalizado = nlp.normalize(texto)
    match = re.search(
        rf"{palabra}\s+(?:llamad[ao]|de|para)\s+([a-z0-9 ]+)", normalizado
    )
    if match:
        nombre = re.sub(r"\s+", " ", match.group(1)).strip(" .,;")
        nombre = nombre.split(" de tipo ")[0]
        nombre = re.sub(r"\s+de\s+(gasto|ingreso)$", "", nombre)
        return nombre[:30]
    return None


def _tipo_cuenta_dicho(texto):
    normalizado = nlp.normalize(texto)
    if word_in := nlp.word_in_text("tarjeta", normalizado):
        return "tarjeta"
    if nlp.word_in_text("inversion", normalizado):
        return "inversion"
    if nlp.word_in_text("ahorro", normalizado) or nlp.word_in_text(
        "ahorros", normalizado
    ):
        return "cuenta_ahorros"
    if any(
        nlp.word_in_text(palabra, normalizado)
        for palabra in ("nequi", "daviplata", "billetera", "digital")
    ):
        return "billetera_digital"
    return "efectivo"


def _proponer_accion(
    conn, usuario_id, texto, intent, entidades, estado, dispositivo_uid
):
    """Prepara una escritura que requiere confirmacion humana."""
    entidades = entidades or {}
    datos = intent
    detalle = ""
    texto_voz = None

    if intent in ("editar_movimiento", "eliminar_movimiento"):
        movimiento = _movimiento_objetivo(conn, usuario_id, texto, entidades)
        if movimiento is None:
            return _respuesta(
                "No encontré un movimiento para esa acción.",
                "aclaracion",
                estado,
                intent=intent,
                dispositivo_uid=dispositivo_uid,
                usuario_id=usuario_id,
                texto=texto,
            )
        resumen = (
            f"{movimiento['tipo']} de {_moneda(movimiento['monto'])}"
            + (f" en {movimiento['categoria']}" if movimiento.get("categoria") else "")
        )
        resumen_voz = (
            f"un {movimiento['tipo']} de {_monto_hablado(movimiento['monto'])}"
            + (f" en {movimiento['categoria']}" if movimiento.get("categoria") else "")
        )
        accion = {
            "tipo": intent,
            "transaccion_id": movimiento["id"],
            "resumen": resumen,
            "resumen_hablado": resumen_voz,
        }
        if intent == "editar_movimiento":
            monto = nlp._entero(entidades.get("monto")) or nlp.parse_amount(texto)
            if not monto:
                return _respuesta(
                    "¿Cuál es el nuevo monto del movimiento?",
                    "aclaracion",
                    estado,
                    intent=intent,
                    dispositivo_uid=dispositivo_uid,
                    usuario_id=usuario_id,
                    texto=texto,
                )
            accion["cambios"] = {"monto": monto}
            detalle = f" y le pongo {_moneda(monto)}"
            detalle_voz = f" y le pongo {_monto_hablado(monto)}"
        else:
            detalle_voz = ""
        mensaje = f"Voy a {'anular' if intent == 'eliminar_movimiento' else 'editar'} {resumen}{detalle}. ¿Está bien?"
        texto_voz = (
            f"Voy a {'anular' if intent == 'eliminar_movimiento' else 'editar'} "
            f"{resumen_voz}{detalle_voz}. ¿Está bien?"
        )
    elif intent == "crear_cuenta":
        nombre = entidades.get("nombre") or _nombre_dicho(texto, "cuenta")
        if not nombre:
            return _respuesta(
                "¿Cómo quieres llamar la cuenta?",
                "aclaracion",
                estado,
                intent=intent,
                dispositivo_uid=dispositivo_uid,
                usuario_id=usuario_id,
                texto=texto,
            )
        tipo_cuenta = entidades.get("tipo_cuenta") or _tipo_cuenta_dicho(texto)
        accion = {
            "tipo": intent,
            "datos": {"nombre": nombre, "tipo_cuenta": tipo_cuenta},
        }
        mensaje = f"Voy a crear la cuenta {nombre} de tipo {tipo_cuenta}. ¿La creo?"
    elif intent == "crear_categoria":
        nombre = entidades.get("nombre") or _nombre_dicho(texto, "categoria")
        if not nombre:
            return _respuesta(
                "¿Cómo quieres llamar la categoría?",
                "aclaracion",
                estado,
                intent=intent,
                dispositivo_uid=dispositivo_uid,
                usuario_id=usuario_id,
                texto=texto,
            )
        tipo = entidades.get("tipo") or nlp.detect_type(texto)
        accion = {"tipo": intent, "datos": {"nombre": nombre, "tipo": tipo}}
        mensaje = f"Voy a crear la categoría {nombre} de {tipo}. ¿La creo?"
    elif intent == "actualizar_presupuesto":
        monto = nlp._entero(entidades.get("monto")) or nlp.parse_amount(texto)
        if not monto:
            return _respuesta(
                "¿Cuál será tu nuevo presupuesto diario?",
                "aclaracion",
                estado,
                intent=intent,
                dispositivo_uid=dispositivo_uid,
                usuario_id=usuario_id,
                texto=texto,
            )
        accion = {"tipo": intent, "datos": {"monto": monto}}
        mensaje = f"Voy a cambiar tu presupuesto diario a {_moneda(monto)}. ¿Está bien?"
        texto_voz = (
            f"Voy a cambiar tu presupuesto diario a {_monto_hablado(monto)}. "
            "¿Está bien?"
        )
    elif intent == "actualizar_perfil":
        monto = nlp._entero(entidades.get("monto")) or nlp.parse_amount(texto)
        if not monto:
            return _respuesta(
                "¿Cuál es tu ingreso mensual?",
                "aclaracion",
                estado,
                intent=intent,
                dispositivo_uid=dispositivo_uid,
                usuario_id=usuario_id,
                texto=texto,
            )
        accion = {"tipo": intent, "datos": {"monto": monto}}
        mensaje = f"Voy a registrar un ingreso mensual de {_moneda(monto)}. ¿Está bien?"
        texto_voz = (
            f"Voy a registrar un ingreso mensual de {_monto_hablado(monto)}. "
            "¿Está bien?"
        )
    elif intent == "eliminar_meta":
        meta = nlp.detect_goal(conn, usuario_id, texto)
        if meta is None:
            return _respuesta(
                "¿Cuál meta quieres eliminar? Dime su nombre exacto.",
                "aclaracion",
                estado,
                datos={"metas": nlp.metas_usuario(conn, usuario_id)},
                intent=intent,
                dispositivo_uid=dispositivo_uid,
                usuario_id=usuario_id,
                texto=texto,
            )
        accion = {"tipo": intent, "meta_id": meta["id"], "nombre": meta["nombre"]}
        mensaje = f"Voy a eliminar la meta {meta['nombre']}. ¿La elimino?"
    else:
        return None

    nuevo_estado = {
        **estado,
        "estado": ESTADO_CONFIRMANDO_ACCION,
        "accion_pendiente": accion,
        "borrador": None,
    }
    guardar_estado(usuario_id, dispositivo_uid, nuevo_estado)
    return _respuesta(
        mensaje,
        "confirmacion",
        nuevo_estado,
        datos={"accion": accion},
        requiere_confirmacion=True,
        intent=intent,
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
        texto_voz=texto_voz,
    )


def _confirmar_accion(conn, usuario_id, texto, estado, dispositivo_uid):
    accion = estado.get("accion_pendiente") or {}
    tipo = accion.get("tipo")
    texto_voz = None
    try:
        if tipo == "eliminar_movimiento":
            resultado = services.delete_transaction(
                conn, usuario_id, accion["transaccion_id"], "voz"
            )
            mensaje = f"Listo, anulé {accion.get('resumen', 'el movimiento')}."
            texto_voz = f"Listo, anulé {accion.get('resumen_hablado', 'el movimiento')}."
        elif tipo == "editar_movimiento":
            resultado = services.update_transaction(
                conn, usuario_id, accion["transaccion_id"], accion.get("cambios") or {}
            )
            mensaje = f"Listo, actualicé {accion.get('resumen', 'el movimiento')}."
            texto_voz = f"Listo, actualicé {accion.get('resumen_hablado', 'el movimiento')}."
        elif tipo == "crear_cuenta":
            resultado = services.create_account(conn, usuario_id, accion.get("datos"))
            mensaje = f"Listo, creé la cuenta {resultado['nombre']}."
        elif tipo == "crear_categoria":
            resultado = services.create_category(conn, usuario_id, accion.get("datos"))
            mensaje = f"Listo, creé la categoría {resultado['nombre']}."
        elif tipo == "actualizar_presupuesto":
            resultado = services.set_daily_budget(
                conn, usuario_id, accion["datos"]["monto"]
            )
            mensaje = f"Listo, tu presupuesto diario quedó en {_moneda(resultado['presupuesto_diario'])}."
            texto_voz = (
                "Listo, tu presupuesto diario quedó en "
                f"{_monto_hablado(resultado['presupuesto_diario'])}."
            )
        elif tipo == "actualizar_perfil":
            resultado = services.set_profile_income(
                conn, usuario_id, accion["datos"]["monto"]
            )
            mensaje = f"Listo, registré un ingreso mensual de {_moneda(resultado['ingreso_trabajo_mensual'])}."
            texto_voz = (
                "Listo, registré un ingreso mensual de "
                f"{_monto_hablado(resultado['ingreso_trabajo_mensual'])}."
            )
        elif tipo == "eliminar_meta":
            services.delete_goal(conn, usuario_id, accion["meta_id"])
            resultado = accion
            mensaje = f"Listo, eliminé la meta {accion.get('nombre')}."
        else:
            return None
    except (ValueError, KeyError) as exc:
        return _respuesta(
            f"No pude completar la acción: {exc}",
            "error",
            estado,
            intent=tipo,
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )
    borrar_estado(usuario_id, dispositivo_uid)
    return _respuesta(
        mensaje,
        "resultado",
        {"estado": ESTADO_INACTIVA, "accion_pendiente": None, "borrador": None},
        datos={"resultado": resultado},
        intent=tipo,
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
        texto_voz=texto_voz,
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
            if not existente.get("texto_voz"):
                existente["texto_voz"] = _texto_para_voz(
                    existente.get("mensaje_nancy")
                )
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
        # Una frase larga no puede confirmar ni cancelar solo porque el LLM
        # asi lo dijo: el usuario podria estar dictando un movimiento nuevo
        # con un estado pendiente abierto. Solo los naturales de confirmacion
        # y cancelacion resuelven la accion.
        if _es_confirmacion(texto) or (intent == "confirmar" and len(nlp.normalize(texto).split()) <= 2):
            return _confirmar(conn, usuario_id, texto, estado, dispositivo_uid)
        if _es_cancelacion(texto) or (intent == "cancelar" and len(nlp.normalize(texto).split()) <= 2):
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

    if intent in (
        "editar_movimiento",
        "eliminar_movimiento",
        "crear_cuenta",
        "crear_categoria",
        "actualizar_presupuesto",
        "actualizar_perfil",
        "eliminar_meta",
    ):
        propuesta = _proponer_accion(
            conn,
            usuario_id,
            texto,
            intent,
            interpretacion.get("entidades") or {},
            estado,
            dispositivo_uid,
        )
        if propuesta is not None:
            return propuesta

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
