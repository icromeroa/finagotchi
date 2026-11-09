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
    "no esta bien",
    "no está bien",
    "esta mal",
    "está mal",
    "me equivoque",
    "me equivoqué",
    "no es de",
    "es de hoy",
    "es de ayer",
    "es de anteayer",
    "la cuenta es",
    "era en",
    "fue hoy",
    "fue ayer",
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


def _describir_movimiento(transaccion, etiqueta_fecha=None):
    tipo = str(transaccion.get("tipo") or "movimiento").lower()
    partes = [f"un {tipo} de {_moneda(transaccion.get('monto'))}"]
    if transaccion.get("categoria"):
        partes.append(f"en {transaccion['categoria']}")
    if transaccion.get("meta"):
        partes.append(f"para la meta {transaccion['meta']}")
    if transaccion.get("cuenta"):
        partes.append(f"desde {transaccion['cuenta']}")
    if etiqueta_fecha:
        partes.append(f"con fecha de {etiqueta_fecha}")
    return " ".join(partes)


def _describir_movimiento_hablado(transaccion, etiqueta_fecha=None):
    """Resumen corto y natural del movimiento para la voz."""
    tipo = str(transaccion.get("tipo") or "movimiento").lower()
    partes = [f"un {tipo} de {_monto_hablado(transaccion.get('monto'))}"]
    if transaccion.get("categoria"):
        partes.append(f"en {str(transaccion['categoria']).lower()}")
    if transaccion.get("meta"):
        partes.append(f"para la meta {transaccion['meta']}")
    if etiqueta_fecha:
        partes.append(f"con fecha de {etiqueta_fecha}")
    return " ".join(partes)


def enriquecer_confirmacion(payload):
    """Completa un mensaje confirmado con lo necesario para que Nancy hable.

    ``services.confirm_message`` se usa tanto desde el flujo conversacional
    (que ya añade ``tipo_respuesta`` y ``texto_voz``) como desde los endpoints
    ``/confirm``. En este segundo caso el cliente recibía el movimiento sin
    frase ni orden de voz y Nancy se quedaba callada. Esta función rellena esos
    campos a partir de las transacciones ya guardadas.
    """
    if not payload:
        return payload
    transacciones = [
        transaccion
        for transaccion in (payload.get("transacciones") or [])
        if not transaccion.get("is_deleted")
    ]
    if transacciones:
        partes = [_describir_movimiento(t) for t in transacciones]
        partes_voz = [_describir_movimiento_hablado(t) for t in transacciones]
        if len(partes) > 1:
            resumen = ", ".join(partes[:-1]) + " y " + partes[-1]
            resumen_voz = ", ".join(partes_voz[:-1]) + " y " + partes_voz[-1]
        else:
            resumen = partes[0]
            resumen_voz = partes_voz[0]
        mensaje = f"Listo. Guardé {resumen}."
        texto_voz = f"Listo. Guardé {resumen_voz}."
    else:
        mensaje = "Listo. Guardé el movimiento."
        texto_voz = mensaje
    payload.setdefault("tipo_respuesta", "resultado")
    payload.setdefault("mensaje_nancy", mensaje)
    payload.setdefault("texto_voz", texto_voz)
    payload.setdefault("estado_conversacion", ESTADO_INACTIVA)
    payload.setdefault("requiere_confirmacion", False)
    return payload


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
    # Validación determinista: el LLM propone, el texto manda. Una cuenta o
    # una fecha que no aparecen en lo que dijo el usuario se descartan.
    normalizado = nlp.normalize(texto)
    monto_texto = nlp.parse_amount(normalizado)
    if monto_texto is not None:
        entidades["monto"] = monto_texto
    cuenta_llm = entidades.get("cuenta")
    if cuenta_llm and not nlp.word_in_text(nlp.normalize(cuenta_llm), normalizado):
        entidades["cuenta"] = None
    fecha_llm = entidades.get("fecha_texto")
    if fecha_llm and not nlp.resolver_rango(texto).get("expresion"):
        entidades["fecha_texto"] = None
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
    if not normalized:
        return False
    if any(nlp.word_in_text(palabra, normalized) for palabra in FRASES_CORRECCION):
        return True
    # Patrones que no caben en una sola palabra suelta: «no es de ayer, es de
    # hoy», «la cuenta es Nequi», «era hoy», «con la categoría de Belleza».
    return bool(
        re.search(
            r"\b(?:no\s+)?(?:es|fue|era)\s+de\s+(?:hoy|ayer|anteayer)\b",
            normalized,
        )
        or re.search(r"\bno\s+(?:es|fue|era)\s+(?:hoy|ayer|anteayer)\b", normalized)
        or re.search(r"\bla cuenta es\b", normalized)
        or re.search(
            r"\b(?:con\s+)?(?:la\s+)?(?:sub)?categor[ií]a\s+(?:de|es|del)\b",
            normalized,
        )
        or re.search(r"\b(?:cambia(?:la)?|pon(?:la)?)\b.*\bcategor", normalized)
    )


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
    local_date_value=None,
    etiqueta_fecha=None,
):
    resultado = _propuesta_movimiento(conn, usuario_id, texto, interpretacion)
    if resultado.get("intent") != "registrar" or not resultado.get("transacciones"):
        mensaje = resultado.get("error") or "No pude entender el movimiento."
        datos = {}
        if resultado.get("meta_sugerida"):
            mensaje = (
                f"No encontré la meta \"{resultado['meta_sugerida']}\". "
                "Dime el nombre exacto de una de tus metas o crea una nueva."
            )
            datos = {"metas": nlp.metas_usuario(conn, usuario_id)}
        elif resultado.get("cuenta_sugerida"):
            datos = {
                "cuentas": [
                    {"id": row["id"], "nombre": row["nombre"]}
                    for row in conn.execute(
                        "SELECT id, nombre FROM cuentas "
                        "WHERE usuario_id = ? ORDER BY id",
                        (usuario_id,),
                    )
                ]
            }
        return _respuesta(
            mensaje,
            "aclaracion",
            {**estado, "estado": ESTADO_INACTIVA},
            datos=datos,
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
        local_date_value=local_date_value,
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
            "local_date_value": local_date_value,
            "etiqueta_fecha": etiqueta_fecha,
            "resumen": _describir_movimiento(transaccion, etiqueta_fecha),
            "resumen_hablado": _describir_movimiento_hablado(
                transaccion, etiqueta_fecha
            ),
        },
        "borrador": None,
    }
    _recordar(nuevo_estado, texto, "confirmacion")
    guardar_estado(usuario_id, dispositivo_uid, nuevo_estado)
    mensaje = (
        f"¿Registro {_describir_movimiento(transaccion, etiqueta_fecha)}? "
        "Puedes decir sí, está bien, ok, o corregirlo."
    )
    return _respuesta(
        mensaje,
        "confirmacion",
        nuevo_estado,
        datos={"transaccion": transaccion, "rango": {"etiqueta": etiqueta_fecha}}
        if etiqueta_fecha
        else {"transaccion": transaccion},
        requiere_confirmacion=True,
        payload=payload,
        intent="registrar",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
        texto_voz=(
            f"¿Registro {_describir_movimiento_hablado(transaccion, etiqueta_fecha)}?"
        ),
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
    # «Con la categoría de Belleza» sin categoría en el catálogo: proponer
    # crearla aplicando al movimiento pendiente tras la confirmación.
    nombre_categoria = _nombre_dicho(texto, "categoria")
    if nombre_categoria and re.search(
        r"\b(?:con\s+)?(?:la\s+)?(?:sub)?categor[ií]a\s+(?:de|es|del)\b",
        nlp.normalize(texto),
    ):
        existe = nlp.detect_category_explicit(
            conn, usuario_id, texto, actual.get("tipo") or "gasto"
        )
        if existe is None:
            propuesta = _proponer_accion(
                conn,
                usuario_id,
                texto,
                "crear_categoria",
                entidades,
                estado,
                dispositivo_uid,
            )
            if propuesta is not None:
                return propuesta
    tipos_validos = ("gasto", "ingreso", "ahorro")
    cambios = {}

    monto = nlp.parse_amount(nlp.normalize(texto))
    if monto is None:
        monto = nlp._entero(entidades.get("monto"))
    if monto is not None:
        cambios["monto"] = monto

    # Solo se cambia el tipo si se dijo explícitamente; si no, se conserva.
    nuevo_tipo = str(entidades.get("tipo") or "").strip().lower()
    if nuevo_tipo not in tipos_validos:
        nuevo_tipo = nlp.detect_type_explicit(texto)
    if nuevo_tipo in tipos_validos and nuevo_tipo != actual.get("tipo"):
        cambios["tipo"] = nuevo_tipo
    tipo_final = cambios.get("tipo") or actual.get("tipo")

    if tipo_final == "ahorro":
        cambios.setdefault("categoria_id", None)
        if entidades.get("meta") or nlp.menciona_meta(texto):
            meta = nlp.coincide_en_catalogo(
                entidades.get("meta"), nlp.metas_usuario(conn, usuario_id)
            ) or nlp.detect_goal(conn, usuario_id, texto)
            if meta is not None:
                cambios["meta_id"] = meta["id"]
    else:
        categoria = None
        if entidades.get("categoria"):
            categoria = nlp.coincide_en_catalogo(
                entidades["categoria"],
                [
                    {"id": row["id"], "nombre": row["nombre"], "tipo": row["tipo"]}
                    for row in conn.execute(
                        "SELECT id, nombre, tipo FROM categorias "
                        "WHERE usuario_id = ? AND activa = 1",
                        (usuario_id,),
                    )
                ],
            )
        if categoria is None:
            categoria = nlp.detect_category_explicit(
                conn, usuario_id, texto, tipo_final
            )
        if categoria is not None:
            cambios["categoria_id"] = categoria["id"]

    # Cuenta y meta solo cuando se mencionan: «es de hoy» no mueve el dinero.
    cuenta = None
    if entidades.get("cuenta"):
        cuenta = nlp.coincide_en_catalogo(
            entidades["cuenta"],
            [
                {"id": row["id"], "nombre": row["nombre"]}
                for row in conn.execute(
                    "SELECT id, nombre FROM cuentas WHERE usuario_id = ? ORDER BY id",
                    (usuario_id,),
                )
            ],
        )
    if cuenta is None:
        cuenta = nlp.detect_account_explicit(conn, usuario_id, texto)
    if cuenta is not None:
        cambios["cuenta_id"] = cuenta["id"]

    fecha_iso, etiqueta_nueva, error_fecha = _fecha_de_texto(
        entidades.get("fecha_texto") or texto
    )
    if error_fecha:
        return _respuesta(
            error_fecha,
            "aclaracion",
            estado,
            intent="corregir",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )
    if fecha_iso is not None:
        cambios["fecha_local"] = fecha_iso

    # Si se repitió el movimiento completo, el concepto pasa a ser esa frase;
    # una corrección parcial («la cuenta es Nequi») conserva el original.
    if monto is not None:
        cambios["concepto"] = texto[:255]

    if not cambios:
        return _respuesta(
            "¿Qué dato quieres corregir: el monto, la categoría, la cuenta, "
            "la meta o la fecha?",
            "aclaracion",
            estado,
            intent="corregir",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )
    try:
        services.update_transaction(conn, usuario_id, actual["id"], cambios)
    except ValueError as exc:
        return _respuesta(
            f"No pude corregir el movimiento: {exc}",
            "aclaracion",
            estado,
            intent="corregir",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )
    payload = services.message_payload(conn, usuario_id, message_id)
    transaccion = payload["transacciones"][0]
    if "fecha_local" in cambios:
        etiqueta_fecha = etiqueta_nueva
        fecha_guardada = cambios["fecha_local"]
    else:
        etiqueta_fecha = accion.get("etiqueta_fecha")
        fecha_guardada = accion.get("local_date_value")
    nuevo_estado = {
        **estado,
        "estado": ESTADO_CONFIRMANDO_MOVIMIENTO,
        "accion_pendiente": {
            "tipo": "confirmar_mensaje",
            "message_id": message_id,
            "texto": texto,
            "local_date_value": fecha_guardada,
            "etiqueta_fecha": etiqueta_fecha,
            "resumen": _describir_movimiento(transaccion, etiqueta_fecha),
            "resumen_hablado": _describir_movimiento_hablado(
                transaccion, etiqueta_fecha
            ),
        },
    }
    guardar_estado(usuario_id, dispositivo_uid, nuevo_estado)
    return _respuesta(
        "Corregido: "
        f"{_describir_movimiento(transaccion, etiqueta_fecha)}. "
        "¿Está correcto ahora?",
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
            f"¿Registro {_describir_movimiento_hablado(transaccion, etiqueta_fecha)}?"
        ),
    )


# ---------------------------------------------------------------------------
# Consultas simples
# ---------------------------------------------------------------------------
def _rango_consulta(texto, interpretacion):
    """Resuelve la fecha de una consulta sin confiar en el cálculo del LLM."""
    entidades = (interpretacion or {}).get("entidades") or {}
    fecha_texto = str(entidades.get("fecha_texto") or "").strip()
    rango = nlp.resolver_rango(fecha_texto or texto)
    if not rango.get("expresion"):
        periodo = str(entidades.get("periodo") or "").strip().lower()
        if periodo in ("hoy", "semana", "mes"):
            rango = nlp.resolver_rango(periodo)
    return rango


def _periodo_legado(rango, hoy):
    """Alias para clientes y pruebas que todavía leen ``datos.periodo``."""
    expresion = str(rango.get("expresion") or "").strip().lower()
    if rango["alcance"] == "semana" and expresion.startswith("esta semana"):
        return "semana"
    if rango["alcance"] == "mes" and expresion == "este mes":
        return "mes"
    if rango["desde"] == rango["hasta"] == hoy:
        return "hoy"
    return rango["alcance"]


def _frase_rango(rango, hoy):
    """Prefijo natural para hablar de un rango sin decir «en hoy»."""
    if rango["desde"] == rango["hasta"] == hoy:
        return "Hoy"
    etiqueta = rango["etiqueta"]
    if etiqueta == "ayer":
        return "Ayer"
    if etiqueta == "anteayer":
        return "Anteayer"
    if etiqueta.startswith("esta semana"):
        return "Esta semana"
    if etiqueta in ("este mes", "el mes pasado", "la semana pasada"):
        return etiqueta[0].upper() + etiqueta[1:]
    if etiqueta.startswith("del "):
        # «Del 3 al 5 de mayo registraste…», no «En del 3…».
        return etiqueta[0].upper() + etiqueta[1:]
    return f"En {etiqueta}"


def _fecha_de_texto(fecha_texto):
    """Valida una expresión temporal de día. Devuelve ``(iso, etiqueta, error)``."""
    if not str(fecha_texto or "").strip():
        return None, None, None
    rango = nlp.resolver_rango(fecha_texto)
    if not rango.get("expresion") or rango.get("alcance") != "dia":
        return None, None, None
    hoy = date_cls.fromisoformat(services.local_date())
    try:
        fecha = date_cls.fromisoformat(rango["desde"])
    except (TypeError, ValueError):
        return None, None, None
    if fecha > hoy:
        return (
            None,
            None,
            "Todavía no puedo registrar movimientos con fecha futura.",
        )
    if fecha < hoy - timedelta(days=365):
        return (
            None,
            None,
            "Solo puedo registrar movimientos de los últimos 365 días.",
        )
    etiqueta = None if fecha == hoy else rango["etiqueta"]
    return fecha.isoformat(), etiqueta, None


def _fecha_movimiento(interpretacion):
    """Valida la fecha dictada para registrar un movimiento.

    Devuelve ``(fecha_iso, etiqueta, error)``. Solo se aceptan fechas entre
    hoy y 365 días atrás; el futuro se rechaza antes de crear el pendiente.
    """
    entidades = (interpretacion or {}).get("entidades") or {}
    return _fecha_de_texto(entidades.get("fecha_texto"))


def _consulta_balance(conn, usuario_id, rango, estado, dispositivo_uid, texto):
    hoy = services.local_date()
    desde, hasta = rango["desde"], rango["hasta"]
    if desde == hasta:
        base = services.metrics_daily(conn, usuario_id, desde)
        resumen = {
            "desde": desde,
            "hasta": hasta,
            "total_ingresos": base.get("total_ingresos", 0),
            "total_gastos": base.get("total_gastos", 0),
            "total_ahorrado": base.get("total_ahorrado", 0),
            "balance_neto": base.get("balance_neto", 0),
            "cupo_restante": base.get("cupo_restante"),
            "presupuesto_diario": base.get("presupuesto_diario"),
            "num_registros": base.get("num_registros", 0),
        }
        if desde != hoy:
            # El cupo diario solo tiene sentido para el día de hoy; en una
            # consulta histórica no se habla de «lo que te queda».
            resumen["cupo_restante"] = None
            resumen["presupuesto_diario"] = None
    else:
        totales = services.period_totals(conn, usuario_id, desde, hasta)
        resumen = {
            "desde": desde,
            "hasta": hasta,
            "total_ingresos": totales["ingresos"],
            "total_gastos": totales["gastos"],
            "total_ahorrado": totales["ahorro"],
            "balance_neto": totales["balance_neto"],
            "cupo_restante": None,
            "presupuesto_diario": None,
            "num_registros": totales["num_registros"],
        }

    if desde == hasta and desde == hoy:
        prefijo = "Hoy"
        verbo = "llevas"
    elif desde == hasta and rango["etiqueta"] == "ayer":
        prefijo = "Ayer"
        verbo = "registraste"
    elif desde == hasta:
        prefijo = f"El {rango['etiqueta']}"
        verbo = "registraste"
    else:
        prefijo = rango["etiqueta"][0].upper() + rango["etiqueta"][1:]
        verbo = "registraste"
    mensaje = (
        f"{prefijo} {verbo} {_moneda(resumen['total_gastos'])} en gastos, "
        f"{_moneda(resumen['total_ingresos'])} en ingresos y "
        f"{_moneda(resumen['total_ahorrado'])} en ahorro. "
        f"El balance es {_moneda(resumen['balance_neto'])}."
    )
    texto_voz = (
        f"{prefijo} {verbo} {_monto_hablado(resumen['total_gastos'])} en gastos, "
        f"{_monto_hablado(resumen['total_ingresos'])} en ingresos y "
        f"{_monto_hablado(resumen['total_ahorrado'])} en ahorro. "
        f"El balance es {_monto_hablado(resumen['balance_neto'])}."
    )
    if resumen.get("cupo_restante") is not None:
        mensaje += f" Te queda un cupo diario de {_moneda(resumen['cupo_restante'])}."
        texto_voz += (
            f" Te queda un cupo diario de "
            f"{_monto_hablado(resumen['cupo_restante'])}."
        )
    estado = {**estado, "estado": ESTADO_INACTIVA, "accion_pendiente": None}
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos={
            "periodo": _periodo_legado(rango, hoy),
            "rango": rango,
            "resumen": resumen,
        },
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


def _consulta_pendientes(conn, usuario_id, estado, dispositivo_uid, texto):
    pendientes = services.pending_transactions(conn, usuario_id)
    if not pendientes:
        mensaje = "No tienes movimientos pendientes por confirmar."
        texto_voz = mensaje
    else:
        detalle = "; ".join(
            _describir_movimiento(movimiento) for movimiento in pendientes[:5]
        )
        mensaje = (
            f"Tienes {len(pendientes)} movimiento"
            f"{'' if len(pendientes) == 1 else 's'} pendiente"
            f"{'' if len(pendientes) == 1 else 's'} por confirmar: {detalle}."
        )
        # La voz lee solo el conteo y el más reciente; el detalle queda
        # en pantalla, como en las consultas por rango.
        texto_voz = (
            f"Tienes {len(pendientes)} movimiento"
            f"{'' if len(pendientes) == 1 else 's'} pendiente"
            f"{'' if len(pendientes) == 1 else 's'} por confirmar: "
            f"{_describir_movimiento_hablado(pendientes[0])}."
        )
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos={"pendientes": pendientes},
        intent="consultar_pendientes",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
        texto_voz=texto_voz,
    )


def _recuperar_accion_orfana(conn, usuario_id, estado, dispositivo_uid, texto):
    """Reconstruye la acción pendiente desde la base si el estado se perdió.

    Devuelve ``(estado, aclaracion)``. Si hay un solo pendiente con mensaje,
    guarda el estado reconstruido y devuelve aclaración None. Si hay varios,
    devuelve una aclaración sin confirmar nada. Si no hay ninguno, deja el
    estado intacto para que el flujo normal responda.
    """
    pendientes = [
        p
        for p in services.pending_transactions(conn, usuario_id)
        if p.get("mensaje_id")
    ]
    if not pendientes:
        return estado, None
    if len(pendientes) > 1:
        respuesta = _respuesta(
            f"Tienes {len(pendientes)} movimientos pendientes por confirmar. "
            "Pregúntame qué tienes pendiente para verlos antes de confirmar.",
            "aclaracion",
            estado,
            datos={"pendientes": pendientes},
            intent="requiere_aclaracion",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
        )
        return estado, respuesta
    pendiente = pendientes[0]
    payload = services.message_payload(conn, usuario_id, pendiente["mensaje_id"])
    if not payload or not payload.get("transacciones"):
        return estado, None
    transaccion = payload["transacciones"][0]
    fecha_local = transaccion.get("fecha_local")
    hoy = services.local_date()
    if fecha_local == hoy:
        etiqueta_fecha = None
    elif fecha_local:
        try:
            dias = (
                date_cls.fromisoformat(hoy) - date_cls.fromisoformat(fecha_local)
            ).days
        except (TypeError, ValueError):
            dias = None
        etiqueta_fecha = (
            "ayer"
            if dias == 1
            else ("anteayer" if dias == 2 else _fecha_hablada(fecha_local))
        )
    else:
        etiqueta_fecha = None
    nuevo_estado = {
        **estado,
        "estado": ESTADO_CONFIRMANDO_MOVIMIENTO,
        "accion_pendiente": {
            "tipo": "confirmar_mensaje",
            "message_id": pendiente["mensaje_id"],
            "texto": transaccion.get("texto_transcrito") or texto,
            "local_date_value": fecha_local,
            "etiqueta_fecha": etiqueta_fecha,
            "resumen": _describir_movimiento(transaccion, etiqueta_fecha),
            "resumen_hablado": _describir_movimiento_hablado(
                transaccion, etiqueta_fecha
            ),
        },
    }
    guardar_estado(usuario_id, dispositivo_uid, nuevo_estado)
    return nuevo_estado, None


def _consulta_cuentas(conn, usuario_id, estado, dispositivo_uid, texto):
    cuentas = services.accounts_summary(conn, usuario_id)
    if cuentas:
        base = [c for c in cuentas if c.get("es_sistema")]
        propias = [c for c in cuentas if not c.get("es_sistema")]

        def _detalle(lista):
            return "; ".join(
                f"{cuenta['nombre']}: {_moneda(cuenta.get('saldo_actual'))}"
                for cuenta in lista[:6]
            )

        def _detalle_voz(lista):
            return "; ".join(
                f"{cuenta['nombre']}: {_monto_hablado(cuenta.get('saldo_actual'))}"
                for cuenta in lista[:6]
            )

        mensaje = ""
        texto_voz = ""
        if base:
            mensaje = f"Tus cuentas base son: {_detalle(base)}."
            texto_voz = f"Tus cuentas base son: {_detalle_voz(base)}."
        if propias:
            frase = f"Tus cuentas propias son: {_detalle(propias)}."
            frase_voz = f"Tus cuentas propias son: {_detalle_voz(propias)}."
            mensaje = f"{mensaje} {frase}".strip()
            texto_voz = f"{texto_voz} {frase_voz}".strip()
        if not mensaje:
            mensaje = f"Tus cuentas son: {_detalle(cuentas)}."
            texto_voz = f"Tus cuentas son: {_detalle_voz(cuentas)}."
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
    normalizado = nlp.normalize(texto)
    pedido = nlp.detect_type_explicit(normalizado)
    if "ahorro" in normalizado and pedido is None:
        mensaje = (
            "El ahorro usa metas, no categorías. "
            "Tus categorías son de gasto o de ingreso."
        )
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
    if pedido in ("gasto", "ingreso"):
        categorias = [c for c in categorias if c.get("tipo") == pedido]
    if not categorias:
        mensaje = "No tienes categorías."
        texto_voz = mensaje
    else:
        def _ordenadas(lista):
            return sorted(
                lista,
                key=lambda c: (-(c.get("num_registros") or 0), -(c.get("total") or 0)),
            )

        def _detalle(categoria):
            return (
                f"{categoria['nombre']} ({categoria.get('num_registros') or 0} "
                f"registros, {_moneda(categoria.get('total'))})"
            )

        def _detalle_voz(categoria):
            registros = categoria.get("num_registros") or 0
            frase_registros = (
                f"{registros} registro"
                if registros == 1
                else f"{registros} registros"
            )
            return (
                f"{categoria['nombre']}: {frase_registros}, "
                f"{_monto_hablado(categoria.get('total'))}"
            )

        grupos = []
        grupos_voz = []
        for tipo in ("gasto", "ingreso"):
            lista = _ordenadas(
                [c for c in categorias if c.get("tipo") == tipo]
            )
            if not lista:
                continue
            grupos.append(f"{tipo.capitalize()}: " + "; ".join(_detalle(c) for c in lista[:6]))
            grupos_voz.append(
                f"{tipo.capitalize()}: "
                + "; ".join(_detalle_voz(c) for c in lista[:3])
            )
        mensaje = "Tus categorías son: " + ". ".join(grupos) + "."
        texto_voz = "Tus categorías: " + ". ".join(grupos_voz) + "."
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos={"categorias": categorias},
        intent="consultar_categorias",
        dispositivo_uid=dispositivo_uid,
        usuario_id=usuario_id,
        texto=texto,
        texto_voz=texto_voz,
    )


def _consulta_movimientos(
    conn, usuario_id, rango, estado, dispositivo_uid, texto, recientes=False
):
    """Lista movimientos de un rango; sin expresión temporal usa los recientes.

    La voz recibe solo el resumen del rango. El detalle completo queda en
    ``datos.movimientos`` para que la pantalla lo muestre.
    """
    hoy = services.local_date()
    resumen = None
    if recientes or not rango.get("expresion"):
        movimientos = services.recent_transactions(conn, usuario_id, limit=8)
        datos = {"movimientos": movimientos}
        if movimientos:
            detalle = "; ".join(
                f"{movimiento['tipo']} de {_moneda(movimiento['monto'])}"
                + (
                    f" en {movimiento['categoria']}"
                    if movimiento.get("categoria")
                    else ""
                )
                for movimiento in movimientos[:6]
            )
            detalle_voz = "; ".join(
                f"{movimiento['tipo']} de {_monto_hablado(movimiento['monto'])}"
                + (
                    f" en {movimiento['categoria']}"
                    if movimiento.get("categoria")
                    else ""
                )
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
            datos=datos,
            intent="consultar_movimientos",
            dispositivo_uid=dispositivo_uid,
            usuario_id=usuario_id,
            texto=texto,
            texto_voz=texto_voz,
        )

    desde, hasta = rango["desde"], rango["hasta"]
    movimientos = services.transactions_between(conn, usuario_id, desde, hasta)
    totales = services.period_totals(conn, usuario_id, desde, hasta)
    resumen = {
        "desde": desde,
        "hasta": hasta,
        "total_ingresos": totales["ingresos"],
        "total_gastos": totales["gastos"],
        "total_ahorrado": totales["ahorro"],
        "balance_neto": totales["balance_neto"],
        "num_registros": totales["num_registros"],
    }
    datos = {
        "periodo": _periodo_legado(rango, hoy),
        "rango": rango,
        "resumen": resumen,
        "movimientos": movimientos,
    }
    frase = _frase_rango(rango, hoy)
    if not movimientos:
        etiqueta = rango["etiqueta"]
        if etiqueta.startswith("del "):
            mensaje = f"No encontré movimientos {etiqueta}."
        else:
            mensaje = f"No encontré movimientos para {etiqueta}."
        texto_voz = mensaje
    else:
        cantidad = len(movimientos)
        detalle = "; ".join(
            f"{movimiento['tipo']} de {_moneda(movimiento['monto'])}"
            + (
                f" en {movimiento['categoria']}"
                if movimiento.get("categoria")
                else ""
            )
            for movimiento in movimientos[:6]
        )
        if cantidad > 6:
            detalle += f"; y {cantidad - 6} más"
        mensaje = (
            f"{frase} registraste {cantidad} movimiento"
            + ("" if cantidad == 1 else "s")
            + f": {detalle}."
        )
        texto_voz = (
            f"{frase} registraste {cantidad} movimiento"
            + ("" if cantidad == 1 else "s")
            + f". Gastos: {_monto_hablado(resumen['total_gastos'])}. "
            f"Ingresos: {_monto_hablado(resumen['total_ingresos'])}. "
            f"Ahorro: {_monto_hablado(resumen['total_ahorrado'])}."
        )
    return _respuesta(
        mensaje,
        "consulta",
        estado,
        datos=datos,
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
        "balance de esta semana; ¿cómo van mis metas?; ¿qué tengo pendiente?; "
        "o cierra el día."
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
        rf"(?:sub)?{palabra}\b\s+"
        rf"(?:(?:esta|la|una|un|nueva|nuevo)\s+)?"
        rf"(?:llamad[ao]|de|para|como)?\s*([a-z0-9 ]+)",
        normalizado,
    )
    if match:
        nombre = re.sub(r"\s+", " ", match.group(1)).strip(" .,;")
        nombre = nombre.split(" de tipo ")[0]
        nombre = re.sub(r"\s+(?:de|en|como)\s+(?:gasto|ingreso|ahorro)$", "", nombre)
        nombre = nombre.split(" de gasto")[0].split(" de ingreso")[0]
        if nombre and nombre not in (
            "gasto", "ingreso", "ahorro", "tipo", "de", "en", "la", "mi",
        ):
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
        if tipo not in ("gasto", "ingreso"):
            return _respuesta(
                "El ahorro usa metas, no categorías. "
                "¿La creo como gasto o como ingreso?",
                "aclaracion",
                estado,
                intent=intent,
                dispositivo_uid=dispositivo_uid,
                usuario_id=usuario_id,
                texto=texto,
            )
        accion = {"tipo": intent, "datos": {"nombre": nombre, "tipo": tipo}}
        pendiente = estado.get("accion_pendiente") or {}
        if pendiente.get("tipo") == "confirmar_mensaje" and pendiente.get("message_id"):
            # Crear la categoría no abandona el movimiento pendiente:
            # al confirmar, la categoría se aplica a ese movimiento.
            accion["aplicar_a_message_id"] = pendiente["message_id"]
            accion["aplicar_a_local_date"] = pendiente.get("local_date_value")
            accion["aplicar_a_etiqueta"] = pendiente.get("etiqueta_fecha")
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
            aplicar_a = accion.get("aplicar_a_message_id")
            if aplicar_a:
                payload_mov = services.message_payload(conn, usuario_id, aplicar_a)
                if payload_mov and payload_mov.get("transacciones"):
                    transaccion_id = payload_mov["transacciones"][0]["id"]
                    services.update_transaction(
                        conn,
                        usuario_id,
                        transaccion_id,
                        {"categoria_id": resultado["id"]},
                    )
                payload_mov = services.message_payload(conn, usuario_id, aplicar_a)
                if payload_mov and payload_mov.get("transacciones"):
                    transaccion = payload_mov["transacciones"][0]
                    etiqueta_fecha = accion.get("aplicar_a_etiqueta")
                    nuevo_estado = {
                        **estado,
                        "estado": ESTADO_CONFIRMANDO_MOVIMIENTO,
                        "accion_pendiente": {
                            "tipo": "confirmar_mensaje",
                            "message_id": aplicar_a,
                            "texto": texto,
                            "local_date_value": accion.get("aplicar_a_local_date"),
                            "etiqueta_fecha": etiqueta_fecha,
                            "resumen": _describir_movimiento(transaccion, etiqueta_fecha),
                            "resumen_hablado": _describir_movimiento_hablado(
                                transaccion, etiqueta_fecha
                            ),
                        },
                    }
                    guardar_estado(usuario_id, dispositivo_uid, nuevo_estado)
                    return _respuesta(
                        f"{mensaje} Ahora, "
                        f"¿Registro {_describir_movimiento(transaccion, etiqueta_fecha)}?",
                        "confirmacion",
                        nuevo_estado,
                        datos={"transaccion": transaccion},
                        requiere_confirmacion=True,
                        payload=payload_mov,
                        intent="registrar",
                        dispositivo_uid=dispositivo_uid,
                        usuario_id=usuario_id,
                        texto=texto,
                        texto_voz=(
                            f"{mensaje} Ahora, "
                            f"¿Registro {_describir_movimiento_hablado(transaccion, etiqueta_fecha)}?"
                        ),
                    )
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
    if not accion and intent != "consultar_pendientes" and (
        intent in ("confirmar", "cancelar", "corregir")
        or _es_confirmacion(texto)
        or _es_cancelacion(texto)
        or _es_correccion(texto)
    ):
        # El estado vive en memoria: si el backend se reinicio, un
        # pendiente puede seguir en la base sin accion en memoria.
        estado, aclaracion = _recuperar_accion_orfana(
            conn, usuario_id, estado, dispositivo_uid, texto
        )
        if aclaracion is not None:
            return aclaracion
        accion = estado.get("accion_pendiente") or {}
    if accion:
        # Una frase larga no puede confirmar ni cancelar solo porque el LLM
        # asi lo dijo: el usuario podria estar dictando un movimiento nuevo
        # con un estado pendiente abierto. Solo los naturales de confirmacion
        # y cancelacion resuelven la accion.
        es_correccion = _es_correccion(texto)
        if intent == "consultar_pendientes":
            # Consultar no resuelve la acción pendiente: se conserva.
            return _consulta_pendientes(
                conn, usuario_id, estado, dispositivo_uid, texto
            )
        if (_es_confirmacion(texto) or (intent == "confirmar" and len(nlp.normalize(texto).split()) <= 2)) and not es_correccion:
            return _confirmar(conn, usuario_id, texto, estado, dispositivo_uid)
        if (_es_cancelacion(texto) or (intent == "cancelar" and len(nlp.normalize(texto).split()) <= 2)) and not (es_correccion and accion.get("tipo") == "confirmar_mensaje"):
            return _cancelar(conn, usuario_id, texto, estado, dispositivo_uid)
        if accion.get("tipo") == "confirmar_mensaje" and (
            intent == "corregir" or _es_correccion(texto)
        ):
            corregido = _corregir_movimiento(
                conn, usuario_id, texto, interpretacion, estado, dispositivo_uid
            )
            if corregido is not None:
                return corregido
        if accion.get("tipo") == "confirmar_mensaje" and intent in (
            "registrar_movimiento",
            "registrar",
        ):
            # Una frase de registro completa con un pendiente abierto no es
            # una confirmación: reemplaza el pendiente en vez de dejar dos
            # borradores huérfanos. El nuevo movimiento queda pendiente de
            # confirmación como cualquier otro.
            propuesta = _propuesta_movimiento(conn, usuario_id, texto, interpretacion)
            if propuesta.get("intent") == "registrar" and propuesta.get("transacciones"):
                services.discard_message(
                    conn, usuario_id, accion.get("message_id")
                )
                estado = {**estado, "accion_pendiente": None}
                # Seguir al bloque de registro: crea el nuevo pendiente.
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
        local_date_value, etiqueta_fecha, error_fecha = _fecha_movimiento(
            interpretacion
        )
        if error_fecha:
            return _respuesta(
                error_fecha,
                "aclaracion",
                {**estado, "estado": ESTADO_INACTIVA},
                intent="requiere_aclaracion",
                dispositivo_uid=dispositivo_uid,
                usuario_id=usuario_id,
                texto=texto,
            )
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
            local_date_value=local_date_value,
            etiqueta_fecha=etiqueta_fecha,
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
        rango = _rango_consulta(texto, interpretacion)
        return _consulta_balance(
            conn, usuario_id, rango, estado, dispositivo_uid, texto
        )
    if intent == "consultar_metas":
        return _consulta_metas(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_plan":
        return _consulta_plan(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_cuentas":
        return _consulta_cuentas(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_pendientes":
        return _consulta_pendientes(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_categorias":
        return _consulta_categorias(conn, usuario_id, estado, dispositivo_uid, texto)
    if intent == "consultar_movimientos":
        rango = _rango_consulta(texto, interpretacion)
        return _consulta_movimientos(
            conn, usuario_id, rango, estado, dispositivo_uid, texto
        )
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
