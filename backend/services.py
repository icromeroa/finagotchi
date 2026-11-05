import calendar
import json
import math
import uuid
from datetime import date as date_cls
from datetime import datetime

from . import nlp
from . import finance_engine, optimization
from .audio import MAX_DURACION_S as MAX_AUDIO_DURACION_S
from .db import (
    BOGOTA,
    clamp,
    dict_row,
    dict_rows,
    get_db,
    iso_utc,
    local_date,
    local_date_from_timestamp,
    now_utc,
)

ALLOWED_TRANSACTION_TYPES = ("gasto", "ingreso", "ahorro")
ALLOWED_TRANSACTION_STATES = ("pendiente", "confirmado", "anulado")
HEALTH_MIN = -35
HEALTH_MAX = 25
PRIORIDAD_MIN = 1
PRIORIDAD_MAX = 5


def parse_priority(value):
    """Normaliza la prioridad de una meta; devuelve None si es invalida."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number < PRIORIDAD_MIN or number > PRIORIDAD_MAX:
        return None
    return number


def parse_date(value):
    try:
        return date_cls.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def transaction_row(conn, user_id, transaction_id):
    return conn.execute(
        """
        SELECT t.*, c.nombre AS categoria, cu.nombre AS cuenta, m.nombre AS meta
        FROM transacciones t
        LEFT JOIN categorias c ON c.usuario_id = t.usuario_id AND c.id = t.categoria_id
        LEFT JOIN cuentas cu ON cu.usuario_id = t.usuario_id AND cu.id = t.cuenta_id
        LEFT JOIN metas m ON m.usuario_id = t.usuario_id AND m.id = t.meta_id
        WHERE t.usuario_id = ? AND t.id = ?
        """,
        (user_id, transaction_id),
    ).fetchone()


def message_por_message_id(conn, user_id, message_id):
    """Busca un mensaje por su identificador externo (idempotencia)."""
    if not message_id:
        return None
    row = conn.execute(
        "SELECT id FROM mensajes_dispositivo WHERE usuario_id = ? AND message_id = ?",
        (user_id, str(message_id)),
    ).fetchone()
    if row is None:
        return None
    return message_payload(conn, user_id, row["id"])


def message_payload(conn, user_id, message_id):
    message = conn.execute(
        "SELECT * FROM mensajes_dispositivo WHERE usuario_id = ? AND id = ?",
        (user_id, message_id),
    ).fetchone()
    if message is None:
        return None
    transactions = conn.execute(
        """
        SELECT t.*, c.nombre AS categoria, cu.nombre AS cuenta
        FROM transacciones t
        LEFT JOIN categorias c ON c.usuario_id = t.usuario_id AND c.id = t.categoria_id
        LEFT JOIN cuentas cu ON cu.usuario_id = t.usuario_id AND cu.id = t.cuenta_id
        WHERE t.usuario_id = ? AND t.mensaje_id = ?
        ORDER BY t.secuencia, t.id
        """,
        (user_id, message_id),
    ).fetchall()
    payload = dict(message)
    payload["transacciones"] = dict_rows(transactions)
    payload["requiere_confirmacion"] = any(
        transaction["estado"] == "pendiente" and not transaction["is_deleted"]
        for transaction in transactions
    )
    return payload


def create_message(
    conn,
    user_id,
    text,
    message_id=None,
    device_id=None,
    device_uid=None,
    origen="app_voz",
    audio_duration_s=None,
    local_date_value=None,
):
    if message_id:
        existing = conn.execute(
            """
            SELECT id FROM mensajes_dispositivo
            WHERE usuario_id = ? AND message_id = ?
            """,
            (user_id, message_id),
        ).fetchone()
        if existing:
            payload = message_payload(conn, user_id, existing["id"])
            payload["duplicado"] = True
            return payload

    if not device_uid and device_id:
        device = conn.execute(
            "SELECT device_uid FROM dispositivos WHERE id = ?", (device_id,)
        ).fetchone()
        device_uid = device["device_uid"] if device else None
    device_uid = device_uid or "app-%s" % user_id

    message_id = message_id or str(uuid.uuid4())
    received_at = now_utc()
    text = (text or "").strip()
    result = nlp.interpret(conn, user_id, text) if text else {
        "intent": "requiere_aclaracion",
        "texto": "",
        "error": "No se recibió texto",
        "transacciones": [],
    }
    if audio_duration_s is not None:
        try:
            audio_duration_s = float(audio_duration_s)
        except (TypeError, ValueError):
            audio_duration_s = None
        if audio_duration_s is not None and not 0.5 <= audio_duration_s <= MAX_AUDIO_DURACION_S:
            audio_duration_s = None
    confidence_values = [
        proposal.get("confianza")
        for proposal in result.get("transacciones", [])
        if proposal.get("confianza") is not None
    ]
    confidence = max(confidence_values) if confidence_values else None

    cursor = conn.execute(
        """
        INSERT INTO mensajes_dispositivo
            (usuario_id, device_id, device_uid, message_id, texto_transcrito,
             origen, duracion_audio_s, confianza_ia, estado, recibido_en,
             procesado_en, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            device_id,
            device_uid,
            message_id,
            text or None,
            origen,
            audio_duration_s,
            confidence,
            "procesado" if result["intent"] == "registrar" else "recibido",
            iso_utc(received_at),
            iso_utc(received_at) if result["intent"] == "registrar" else None,
            result.get("error"),
        ),
    )
    internal_id = cursor.lastrowid
    local_day = local_date_value or local_date(received_at)

    for index, proposal in enumerate(result.get("transacciones", [])):
        conn.execute(
            """
            INSERT INTO transacciones
                (usuario_id, mensaje_id, device_uid, secuencia, tipo, monto,
                 categoria_id, cuenta_id, meta_id, concepto, texto_transcrito,
                 origen, estado, fecha_hora, fecha_local, confianza_ia,
                 creado_en, actualizado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendiente', ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                internal_id,
                device_uid,
                index + 1,
                proposal["tipo"],
                proposal["monto"],
                proposal.get("categoria_id"),
                proposal["cuenta_id"],
                proposal.get("meta_id"),
                proposal.get("concepto") or text[:255],
                text,
                origen,
                iso_utc(received_at),
                local_day,
                proposal.get("confianza"),
                iso_utc(received_at),
                iso_utc(received_at),
            ),
        )
    conn.commit()
    payload = message_payload(conn, user_id, internal_id)
    payload["intent"] = result["intent"]
    payload["origen_interpretacion"] = result.get("origen", "reglas")
    if result.get("proveedor"):
        payload["proveedor_interpretacion"] = result["proveedor"]
    return payload


def log_ai_interaction(
    conn,
    user_id,
    proveedor,
    modelo=None,
    version_prompt=None,
    entrada=None,
    salida=None,
    confianza=None,
    latencia_ms=None,
    tokens_entrada=None,
    tokens_salida=None,
    mensaje_id=None,
):
    """Registra la auditoria de una llamada de IA.

    ``entrada`` y ``salida`` solo deben contener metadatos y texto. El audio
    nunca se persiste.
    """
    cursor = conn.execute(
        """
        INSERT INTO interacciones_ia
            (usuario_id, mensaje_id, proveedor, modelo, version_prompt,
             entrada_json, salida_json, confianza, latencia_ms,
             tokens_entrada, tokens_salida)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            mensaje_id,
            proveedor,
            modelo,
            version_prompt,
            json.dumps(entrada, ensure_ascii=False) if entrada is not None else None,
            json.dumps(salida, ensure_ascii=False) if salida is not None else None,
            confianza,
            latencia_ms,
            tokens_entrada,
            tokens_salida,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def create_device_notification(
    conn,
    user_id,
    device_id,
    tipo,
    titulo,
    mensaje=None,
    mensaje_id=None,
    transaccion_id=None,
    payload=None,
):
    if not device_id:
        return None
    device = conn.execute(
        "SELECT usuario_id FROM dispositivos WHERE id = ?",
        (device_id,),
    ).fetchone()
    if device is None or device["usuario_id"] != user_id:
        return None
    existing = conn.execute(
        """
        SELECT * FROM dispositivos_notificaciones
        WHERE dispositivo_id = ? AND tipo = ?
          AND COALESCE(mensaje_id, 0) = COALESCE(?, 0)
          AND COALESCE(transaccion_id, 0) = COALESCE(?, 0)
        ORDER BY id LIMIT 1
        """,
        (device_id, tipo, mensaje_id, transaccion_id),
    ).fetchone()
    if existing:
        result = dict(existing)
        result["duplicado"] = True
        return result

    cursor = conn.execute(
        """
        INSERT INTO dispositivos_notificaciones
            (dispositivo_id, usuario_id, mensaje_id, transaccion_id, tipo,
             titulo, mensaje, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            device_id,
            user_id,
            mensaje_id,
            transaccion_id,
            tipo,
            titulo,
            mensaje,
            json.dumps(payload, ensure_ascii=False) if payload is not None else None,
        ),
    )
    row = conn.execute(
        "SELECT * FROM dispositivos_notificaciones WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    result = dict(row)
    result["duplicado"] = False
    return result


def device_notifications(conn, user_id, device_id, estado=None, after_id=0, limit=20):
    try:
        limit = max(1, min(int(limit or 20), 100))
        after_id = max(0, int(after_id or 0))
    except (TypeError, ValueError):
        raise ValueError("Los parametros de paginacion no son validos")
    if estado not in (None, "pendiente", "entregada", "leida"):
        raise ValueError("El estado de notificacion no es valido")
    clauses = ["usuario_id = ?", "dispositivo_id = ?"]
    params = [user_id, device_id]
    if estado:
        clauses.append("estado = ?")
        params.append(estado)
    else:
        clauses.append("estado IN ('pendiente','entregada')")
    if after_id:
        clauses.append("id > ?")
        params.append(after_id)
    rows = conn.execute(
        f"""
        SELECT id, dispositivo_id, mensaje_id, transaccion_id, tipo, titulo,
               mensaje, payload_json, estado, creado_en, entregado_en, leido_en
        FROM dispositivos_notificaciones
        WHERE {' AND '.join(clauses)}
        ORDER BY id
        LIMIT ?
        """,
        (*params, limit),
    ).fetchall()
    return dict_rows(rows)


def ack_device_notification(conn, user_id, device_id, notification_id, estado="leida"):
    if estado not in ("entregada", "leida"):
        raise ValueError("El acuse debe ser entregada o leida")
    now = iso_utc()
    row = conn.execute(
        """
        SELECT * FROM dispositivos_notificaciones
        WHERE id = ? AND usuario_id = ? AND dispositivo_id = ?
        """,
        (notification_id, user_id, device_id),
    ).fetchone()
    if row is None:
        return None
    if estado == "entregada":
        if row["estado"] == "pendiente":
            conn.execute(
                """
                UPDATE dispositivos_notificaciones
                SET estado = 'entregada', entregado_en = ?
                WHERE id = ? AND usuario_id = ? AND dispositivo_id = ?
                """,
                (now, notification_id, user_id, device_id),
            )
    elif row["estado"] != "leida":
        conn.execute(
            """
            UPDATE dispositivos_notificaciones
            SET estado = 'leida',
                entregado_en = COALESCE(entregado_en, ?),
                leido_en = ?
            WHERE id = ? AND usuario_id = ? AND dispositivo_id = ?
            """,
            (now, now, notification_id, user_id, device_id),
        )
    conn.commit()
    updated = conn.execute(
        "SELECT * FROM dispositivos_notificaciones WHERE id = ?",
        (notification_id,),
    ).fetchone()
    return dict(updated)


def ack_device_notifications(conn, user_id, device_id, notification_ids, estado="leida"):
    if not isinstance(notification_ids, list) or not notification_ids:
        raise ValueError("Debes enviar una lista de ids")
    updated = 0
    for notification_id in notification_ids:
        try:
            notification_id = int(notification_id)
        except (TypeError, ValueError):
            raise ValueError("Los ids de notificacion no son validos")
        row = ack_device_notification(conn, user_id, device_id, notification_id, estado)
        if row is not None:
            updated += 1
    return updated


def confirm_message(conn, user_id, message_id):
    message = conn.execute(
        "SELECT * FROM mensajes_dispositivo WHERE usuario_id = ? AND id = ?",
        (user_id, message_id),
    ).fetchone()
    if message is None:
        return None
    confirmed_at = iso_utc()
    pending = conn.execute(
        """
        SELECT id FROM transacciones
        WHERE usuario_id = ? AND mensaje_id = ? AND estado = 'pendiente' AND is_deleted = 0
        """,
        (user_id, message_id),
    ).fetchall()
    for row in pending:
        conn.execute(
            """
            UPDATE transacciones
            SET estado = 'confirmado', confirmado_en = ?
            WHERE usuario_id = ? AND id = ?
            """,
            (confirmed_at, user_id, row["id"]),
        )
    conn.execute(
        """
        UPDATE mensajes_dispositivo
        SET estado = 'confirmado'
        WHERE usuario_id = ? AND id = ?
        """,
        (user_id, message_id),
    )
    first_transaction = conn.execute(
        """
        SELECT id FROM transacciones
        WHERE usuario_id = ? AND mensaje_id = ?
        ORDER BY secuencia, id LIMIT 1
        """,
        (user_id, message_id),
    ).fetchone()
    notification = create_device_notification(
        conn,
        user_id,
        message["device_id"],
        "movimiento_registrado",
        "Registro guardado",
        "Se guardo el registro en FinaGotchi",
        mensaje_id=message_id,
        transaccion_id=first_transaction["id"] if first_transaction else None,
        payload={
            "message_id": message["message_id"],
            "transacciones": len(pending),
        },
    )
    conn.commit()
    payload = message_payload(conn, user_id, message_id)
    payload["puntos_otorgados"] = len(pending)
    payload["health"] = health_projection(conn, user_id, local_date())
    if notification:
        payload["notificacion"] = {
            "id": notification["id"],
            "tipo": notification["tipo"],
            "titulo": notification["titulo"],
            "estado": notification["estado"],
            "duplicado": notification["duplicado"],
        }
    return payload


def create_transaction(conn, user_id, data):
    transaction_type = data.get("tipo")
    if transaction_type not in ALLOWED_TRANSACTION_TYPES:
        raise ValueError("Tipo de movimiento inválido")
    try:
        amount = int(data.get("monto"))
    except (TypeError, ValueError):
        raise ValueError("El monto debe ser un entero positivo")
    if amount <= 0:
        raise ValueError("El monto debe ser mayor que cero")

    state = data.get("estado") or "confirmado"
    if state not in ("pendiente", "confirmado"):
        raise ValueError("Estado de movimiento inválido")

    account_id = data.get("cuenta_id")
    if account_id is None:
        account = conn.execute(
            """
            SELECT id FROM cuentas
            WHERE usuario_id = ? AND es_por_defecto = 1
            ORDER BY id LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if account is None:
            raise ValueError("No hay cuenta por defecto")
        account_id = account["id"]
    else:
        account = conn.execute(
            "SELECT id FROM cuentas WHERE usuario_id = ? AND id = ?",
            (user_id, account_id),
        ).fetchone()
        if account is None:
            raise ValueError("La cuenta no existe")
        account_id = account["id"]

    category_id = data.get("categoria_id")
    goal_id = data.get("meta_id")
    if transaction_type == "ahorro":
        category_id = None
    else:
        goal_id = None
        if category_id is None:
            raise ValueError("La categoría es obligatoria")
        category = conn.execute(
            """
            SELECT id, tipo FROM categorias
            WHERE usuario_id = ? AND id = ? AND activa = 1
            """,
            (user_id, category_id),
        ).fetchone()
        if category is None:
            raise ValueError("La categoría no existe o no está activa")
        if category["tipo"] != transaction_type:
            raise ValueError("La categoría no corresponde al tipo de movimiento")
        category_id = category["id"]

    if goal_id is not None:
        goal = conn.execute(
            "SELECT id FROM metas WHERE usuario_id = ? AND id = ? AND is_deleted = 0",
            (user_id, goal_id),
        ).fetchone()
        if goal is None:
            raise ValueError("La meta no existe")

    occurred_at = data.get("fecha_hora")
    if occurred_at:
        try:
            moment = datetime.fromisoformat(str(occurred_at).replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("La fecha y hora no es válida")
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=BOGOTA)
        occurred_utc = moment.astimezone(now_utc().tzinfo)
    else:
        occurred_utc = now_utc()

    local_day = local_date_from_timestamp(iso_utc(occurred_utc))
    timestamp = iso_utc(occurred_utc)
    cursor = conn.execute(
        """
        INSERT INTO transacciones
            (usuario_id, tipo, monto, categoria_id, cuenta_id, meta_id, concepto,
             origen, estado, fecha_hora, fecha_local, confirmado_en, creado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            transaction_type,
            amount,
            category_id,
            account_id,
            goal_id,
            (data.get("concepto") or "")[:255] or None,
            data.get("origen") or "manual",
            state,
            timestamp,
            local_day,
            timestamp if state == "confirmado" else None,
            timestamp,
        ),
    )
    conn.commit()
    row = transaction_row(conn, user_id, cursor.lastrowid)
    return dict(row)


def update_transaction(conn, user_id, transaction_id, data):
    current = transaction_row(conn, user_id, transaction_id)
    if current is None or current["is_deleted"]:
        return None

    allowed = {}
    if "monto" in data:
        try:
            amount = int(data["monto"])
        except (TypeError, ValueError):
            raise ValueError("El monto debe ser un entero positivo")
        if amount <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        allowed["monto"] = amount
    if "concepto" in data:
        allowed["concepto"] = (data.get("concepto") or "")[:255] or None
    if "categoria_id" in data:
        allowed["categoria_id"] = data.get("categoria_id")
    if "cuenta_id" in data:
        account = conn.execute(
            "SELECT id FROM cuentas WHERE usuario_id = ? AND id = ?",
            (user_id, data.get("cuenta_id")),
        ).fetchone()
        if account is None:
            raise ValueError("La cuenta no existe")
        allowed["cuenta_id"] = account["id"]
    if "meta_id" in data:
        goal_id = data.get("meta_id")
        if goal_id is not None:
            goal = conn.execute(
                "SELECT id FROM metas WHERE usuario_id = ? AND id = ? AND is_deleted = 0",
                (user_id, goal_id),
            ).fetchone()
            if goal is None:
                raise ValueError("La meta no existe")
        allowed["meta_id"] = goal_id
    if not allowed:
        return dict(current)

    if "categoria_id" in allowed and allowed["categoria_id"] is not None:
        category = conn.execute(
            """
            SELECT id, tipo FROM categorias
            WHERE usuario_id = ? AND id = ? AND activa = 1
            """,
            (user_id, allowed["categoria_id"]),
        ).fetchone()
        if category is None:
            raise ValueError("La categoría no existe o no está activa")
        if category["tipo"] != current["tipo"]:
            raise ValueError("La categoría no corresponde al tipo de movimiento")
        allowed["categoria_id"] = category["id"]

    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE transacciones SET {assignments}, actualizado_en = ? WHERE usuario_id = ? AND id = ?",
        (*allowed.values(), iso_utc(), user_id, transaction_id),
    )
    conn.commit()
    return dict(transaction_row(conn, user_id, transaction_id))


def delete_transaction(conn, user_id, transaction_id, action="anular", reason=None):
    row = transaction_row(conn, user_id, transaction_id)
    if row is None or row["is_deleted"]:
        return None
    conn.execute(
        """
        UPDATE transacciones
        SET is_deleted = 1, deleted_at = ?, eliminado_via = ?, actualizado_en = ?
        WHERE usuario_id = ? AND id = ?
        """,
        (iso_utc(), action, iso_utc(), user_id, transaction_id),
    )
    conn.commit()
    return dict(transaction_row(conn, user_id, transaction_id))


def restore_transaction(conn, user_id, transaction_id):
    row = transaction_row(conn, user_id, transaction_id)
    if row is None:
        return None
    conn.execute(
        """
        UPDATE transacciones
        SET is_deleted = 0, deleted_at = NULL, eliminado_via = NULL, actualizado_en = ?
        WHERE usuario_id = ? AND id = ?
        """,
        (iso_utc(), user_id, transaction_id),
    )
    conn.commit()
    return dict(transaction_row(conn, user_id, transaction_id))


def day_totals(conn, user_id, date_value):
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) AS ingresos,
            COALESCE(SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END), 0) AS gastos,
            COALESCE(SUM(CASE WHEN tipo = 'ahorro' THEN monto ELSE 0 END), 0) AS ahorro,
            COUNT(*) AS num_registros
        FROM transacciones
        WHERE usuario_id = ? AND fecha_local = ? AND estado = 'confirmado' AND is_deleted = 0
        """,
        (user_id, date_value),
    ).fetchone()
    totals = dict(row)
    totals["balance_neto"] = totals["ingresos"] - totals["gastos"]
    return totals


def budget_for_day(conn, user_id, date_value):
    row = conn.execute(
        """
        SELECT COALESCE((
            SELECT h.monto
            FROM presupuesto_diario_historial h
            WHERE h.usuario_id = ? AND h.fecha_local <= ?
            ORDER BY h.fecha_local DESC LIMIT 1
        ), u.presupuesto_diario) AS monto
        FROM usuarios u WHERE u.id = ?
        """,
        (user_id, date_value, user_id),
    ).fetchone()
    return int(row["monto"] or 0) if row else 0


def approved_category_limits(conn, user_id, date_value):
    month_start = date_value[:7] + "-01"
    rows = conn.execute(
        """
        SELECT pc.categoria_id, c.nombre, pc.monto_limite_mensual,
               p.fecha_inicio, p.fecha_fin
        FROM presupuesto_categoria pc
        JOIN presupuestos p
          ON p.usuario_id = pc.usuario_id AND p.id = pc.presupuesto_id
        JOIN categorias c
          ON c.usuario_id = pc.usuario_id AND c.id = pc.categoria_id
        WHERE pc.usuario_id = ? AND pc.tipo = 'gasto' AND p.aprobado = 1
          AND ? BETWEEN p.fecha_inicio AND p.fecha_fin
        ORDER BY p.fecha_inicio DESC
        """,
        (user_id, month_start),
    ).fetchall()
    limits = {}
    for row in rows:
        if row["categoria_id"] not in limits:
            limits[row["categoria_id"]] = dict(row)
    return list(limits.values())


def spending_by_category(conn, user_id, date_value):
    rows = conn.execute(
        """
        SELECT categoria_id, SUM(monto) AS total
        FROM transacciones
        WHERE usuario_id = ? AND fecha_local = ? AND tipo = 'gasto'
          AND estado = 'confirmado' AND is_deleted = 0
        GROUP BY categoria_id
        """,
        (user_id, date_value),
    ).fetchall()
    return {row["categoria_id"]: int(row["total"] or 0) for row in rows}


def streak_ending_on(conn, user_id, date_value):
    rows = conn.execute(
        """
        SELECT DISTINCT fecha_local FROM transacciones
        WHERE usuario_id = ? AND estado = 'confirmado' AND is_deleted = 0
          AND fecha_local <= ?
        ORDER BY fecha_local DESC
        """,
        (user_id, date_value),
    ).fetchall()
    if not rows:
        return 0
    days = {row["fecha_local"] for row in rows}
    cursor = parse_date(date_value)
    streak = 0
    while cursor and cursor.isoformat() in days:
        streak += 1
        cursor = cursor.fromordinal(cursor.toordinal() - 1)
    return streak


def expected_goal_amount(goal, on_date):
    start = parse_date(str(goal["creado_en"])[:10])
    limit = parse_date(goal["fecha_limite"])
    if start is None or limit is None or on_date < start:
        return 0
    end = min(on_date, limit)
    days = (end - start).days
    frequency = goal["frecuencia_ahorro"]
    if frequency == "diaria":
        periods = days
    elif frequency == "semanal":
        periods = days // 7
    elif frequency == "quincenal":
        periods = days // 15
    else:
        months = (end.year - start.year) * 12 + (end.month - start.month)
        if end.day >= start.day:
            months += 1
        periods = max(0, months)
    return min(int(goal["monto_meta"]), periods * int(goal["aporte_periodico"]))


def goal_health_rules(conn, user_id, date_value, persist=False):
    rules = []
    goals = conn.execute(
        """
        SELECT * FROM metas
        WHERE usuario_id = ? AND is_deleted = 0 AND estado = 'activa'
        """,
        (user_id,),
    ).fetchall()
    parsed_date = parse_date(date_value)
    if parsed_date is None:
        return rules
    for goal in goals:
        saved = conn.execute(
            """
            SELECT COALESCE(SUM(monto), 0) AS total
            FROM transacciones
            WHERE usuario_id = ? AND meta_id = ? AND tipo = 'ahorro'
              AND estado = 'confirmado' AND is_deleted = 0 AND fecha_local <= ?
            """,
            (user_id, goal["id"], date_value),
        ).fetchone()["total"]
        saved = int(saved or 0)
        expected = expected_goal_amount(goal, parsed_date)
        period = date_value[:7]
        if saved >= int(goal["monto_meta"]):
            exists = conn.execute(
                """
                SELECT 1 FROM metas_eventos
                WHERE usuario_id = ? AND meta_id = ? AND tipo = 'cumplida'
                """,
                (user_id, goal["id"]),
            ).fetchone()
            if not exists:
                rules.append(
                    ("META_CUMPLIDA", "meta", 5, "meta", goal["id"], {"meta": goal["nombre"]})
                )
                if persist:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO metas_eventos
                            (usuario_id, meta_id, tipo, periodo_clave, salud_delta, detalle_json)
                        VALUES (?, ?, 'cumplida', ?, 5, ?)
                        """,
                        (user_id, goal["id"], period, json.dumps({"monto_meta": goal["monto_meta"]})),
                    )
                    conn.execute(
                        "UPDATE metas SET estado = 'completada', completada_en = ? WHERE usuario_id = ? AND id = ?",
                        (iso_utc(), user_id, goal["id"]),
                    )
        elif expected > 0 and saved < expected * 0.95:
            exists = conn.execute(
                """
                SELECT 1 FROM metas_eventos
                WHERE usuario_id = ? AND meta_id = ? AND tipo = 'atrasada' AND periodo_clave = ?
                """,
                (user_id, goal["id"], period),
            ).fetchone()
            if not exists:
                rules.append(
                    ("META_ATRASADA", "meta", -5, "meta", goal["id"], {"meta": goal["nombre"]})
                )
                if persist:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO metas_eventos
                            (usuario_id, meta_id, tipo, periodo_clave, salud_delta, detalle_json)
                        VALUES (?, ?, 'atrasada', ?, -5, ?)
                        """,
                        (user_id, goal["id"], period, json.dumps({"esperado": expected, "ahorrado": saved})),
                    )
    return rules


def health_start_for_day(conn, user_id, date_value):
    row = conn.execute(
        """
        SELECT salud_fin FROM cierres_dia
        WHERE usuario_id = ? AND fecha_local < ? AND salud_fin IS NOT NULL
        ORDER BY fecha_local DESC LIMIT 1
        """,
        (user_id, date_value),
    ).fetchone()
    return int(row["salud_fin"]) if row else 100


def calculate_health(conn, user_id, date_value, persist=False):
    start = health_start_for_day(conn, user_id, date_value)
    totals = day_totals(conn, user_id, date_value)
    budget = budget_for_day(conn, user_id, date_value)
    rules = []

    excess = max(0, totals["gastos"] - budget)
    if excess > 0:
        penalty = min(20, math.ceil(excess / 5000) * 2)
        rules.append(("EXCESO_DIARIO", "presupuesto_diario", -penalty, "cierre", None, {"exceso": excess}))

    penalties_by_category = 0
    for limit in approved_category_limits(conn, user_id, date_value):
        spent = spending_by_category(conn, user_id, date_value).get(limit["categoria_id"], 0)
        year, month = int(date_value[:4]), int(date_value[5:7])
        days_in_month = calendar.monthrange(year, month)[1]
        daily_cap = int(limit["monto_limite_mensual"] or 0) / days_in_month
        if spent > daily_cap:
            rules.append(
                (
                    "EXCESO_CATEGORIA",
                    "presupuesto_categoria",
                    -2,
                    "categoria",
                    limit["categoria_id"],
                    {"categoria": limit["nombre"], "gastado": spent, "tope_diario": round(daily_cap, 2)},
                )
            )
            penalties_by_category += 1

    if totals["num_registros"] == 0:
        rules.append(("INACTIVIDAD", "inactividad", -5, "cierre", None, {"dias": 1}))

    streak = streak_ending_on(conn, user_id, date_value)
    if streak in (7, 14, 30):
        bonus = {7: 5, 14: 10, 30: 15}[streak]
        rules.append(("RACHA", "racha", bonus, "sistema", None, {"dias": streak}))

    if excess == 0 and penalties_by_category == 0 and totals["balance_neto"] > 0:
        bonus = min(15, (totals["balance_neto"] // 20000) * 2)
        if bonus:
            rules.append(("BALANCE_POSITIVO", "balance_positivo", bonus, "cierre", None, {}))

    if totals["ahorro"] > 0:
        bonus = min(10, totals["ahorro"] // 20000)
        if bonus:
            rules.append(("AHORRO", "ahorro", bonus, "cierre", None, {"ahorro": totals["ahorro"]}))

    rules.extend(goal_health_rules(conn, user_id, date_value, persist=persist))

    raw_delta = sum(rule[2] for rule in rules)
    capped_delta = max(HEALTH_MIN, min(HEALTH_MAX, raw_delta))
    if capped_delta != raw_delta:
        rules.append(("TOPE_GLOBAL", "ajuste", capped_delta - raw_delta, "sistema", None, {"bruto": raw_delta}))

    current = start
    logged_rules = []
    for code, motive, delta, reference_type, reference_id, detail in rules:
        previous = current
        current = clamp(previous + delta)
        logged_rules.append(
            {
                "codigo": code,
                "motivo": motive,
                "delta_solicitado": delta,
                "salud_anterior": previous,
                "salud_nueva": current,
                "detalle": detail,
            }
        )
        if persist:
            conn.execute(
                """
                INSERT OR IGNORE INTO salud_log
                    (usuario_id, fecha_local, regla_codigo, motivo, salud_anterior,
                     salud_nueva, referencia_tipo, referencia_id, detalle_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    date_value,
                    code,
                    motive,
                    previous,
                    current,
                    reference_type,
                    reference_id,
                    json.dumps(detail, ensure_ascii=False),
                ),
            )

    if budget > 0:
        percentage = int(100 * totals["gastos"] / budget)
    else:
        percentage = 0

    if percentage <= 100:
        grade = "bien"
    elif percentage <= 120:
        grade = "regular"
    else:
        grade = "mal"

    return {
        "salud_inicio": start,
        "delta_bruto": raw_delta,
        "delta": current - start,
        "salud_fin": current,
        "reglas": logged_rules,
        "totales": totals,
        "presupuesto_diario": budget,
        "porcentaje_usado": percentage,
        "calificacion": grade,
        "racha": streak,
    }


def health_projection(conn, user_id, date_value):
    result = calculate_health(conn, user_id, date_value, persist=False)
    return {
        "fecha_local": date_value,
        "salud": result["salud_fin"],
        "salud_inicio": result["salud_inicio"],
        "delta": result["delta"],
        "animo": mood_for_health(result["salud_fin"]),
        "reglas": result["reglas"],
    }


def mood_for_health(health):
    if health <= 20:
        return "CRITICO"
    if health <= 50:
        return "TRISTE"
    if health <= 80:
        return "PREOCUPADO"
    return "FELIZ"


def close_day(conn, user_id, date_value):
    existing = conn.execute(
        "SELECT * FROM cierres_dia WHERE usuario_id = ? AND fecha_local = ?",
        (user_id, date_value),
    ).fetchone()
    if existing:
        return dict(existing)

    pending = conn.execute(
        """
        SELECT COUNT(*) AS total FROM transacciones
        WHERE usuario_id = ? AND fecha_local = ? AND estado = 'pendiente' AND is_deleted = 0
        """,
        (user_id, date_value),
    ).fetchone()["total"]
    if pending:
        raise ValueError("Hay movimientos pendientes sin resolver")

    result = calculate_health(conn, user_id, date_value, persist=True)
    totals = result["totales"]
    cursor = conn.execute(
        """
        INSERT INTO cierres_dia
            (usuario_id, fecha_local, total_ingresos, total_gastos, total_ahorrado,
             balance_neto, presupuesto_diario, porcentaje_usado, calificacion,
             num_registros, salud_inicio, salud_fin, cerrado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            date_value,
            totals["ingresos"],
            totals["gastos"],
            totals["ahorro"],
            totals["balance_neto"],
            result["presupuesto_diario"],
            result["porcentaje_usado"],
            result["calificacion"],
            totals["num_registros"],
            result["salud_inicio"],
            result["salud_fin"],
            iso_utc(),
        ),
    )
    conn.execute(
        """
        UPDATE estado_mascota
        SET salud = ?, ultima_actualizacion = ?
        WHERE usuario_id = ?
        """,
        (result["salud_fin"], iso_utc(), user_id),
    )
    conn.execute(
        """
        UPDATE progreso_etapa
        SET racha_actual = ?, mejor_racha = MAX(mejor_racha, ?), actualizado_en = ?
        WHERE usuario_id = ?
        """,
        (result["racha"], result["racha"], iso_utc(), user_id),
    )
    conn.commit()
    closure = conn.execute(
        "SELECT * FROM cierres_dia WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    payload = dict(closure)
    payload["reglas"] = result["reglas"]
    payload["animo"] = mood_for_health(result["salud_fin"])
    return payload


def home_payload(conn, user_id, incluir_plan=False):
    today = local_date()
    user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()
    mascot = conn.execute(
        "SELECT * FROM v_estado_mascota WHERE usuario_id = ?", (user_id,)
    ).fetchone()
    progress = conn.execute(
        "SELECT * FROM v_progreso_etapa WHERE usuario_id = ?", (user_id,)
    ).fetchone()
    projection = health_projection(conn, user_id, today)
    totals = day_totals(conn, user_id, today)
    budget = budget_for_day(conn, user_id, today)
    points = conn.execute(
        "SELECT COALESCE(SUM(puntos), 0) AS total FROM puntos_log WHERE usuario_id = ?",
        (user_id,),
    ).fetchone()["total"]
    payload = {
        "usuario": {
            "id": user["id"],
            "nombre": user["nombre"],
            "zona_horaria": user["zona_horaria"],
        },
        "mascota": dict(mascot) if mascot else {"salud": 100, "animo": "FELIZ", "nombre": "Nancy"},
        "proyeccion_hoy": projection,
        "hoy": {
            "ingresos": totals["ingresos"],
            "gastos": totals["gastos"],
            "ahorro": totals["ahorro"],
            "balance_neto": totals["balance_neto"],
            "presupuesto_diario": budget,
            "cupo_restante": budget - totals["gastos"],
            "num_registros": totals["num_registros"],
        },
        "progreso": dict(progress) if progress else {},
        "puntos": int(points or 0),
        "fecha_local": today,
    }
    if incluir_plan:
        payload["plan_ahorro"] = plan_resumen(conn, user_id, today)
    return payload


def metrics_daily(conn, user_id, date_value):
    row = conn.execute(
        "SELECT * FROM v_balance_diario WHERE usuario_id = ? AND fecha_local = ?",
        (user_id, date_value),
    ).fetchone()
    if row:
        return dict(row)
    totals = day_totals(conn, user_id, date_value)
    budget = budget_for_day(conn, user_id, date_value)
    return {
        "usuario_id": user_id,
        "fecha_local": date_value,
        "total_ingresos": totals["ingresos"],
        "total_gastos": totals["gastos"],
        "total_ahorrado": totals["ahorro"],
        "balance_neto": totals["balance_neto"],
        "presupuesto_diario": budget,
        "cupo_restante": budget - totals["gastos"],
        "porcentaje_usado": int(100 * totals["gastos"] / budget) if budget else None,
        "num_registros": totals["num_registros"],
    }


def categories_breakdown(conn, user_id, date_value):
    rows = conn.execute(
        """
        SELECT COALESCE(c.nombre, 'Sin categoría') AS categoria, c.icono,
               SUM(t.monto) AS total, COUNT(*) AS num_registros
        FROM transacciones t
        LEFT JOIN categorias c ON c.usuario_id = t.usuario_id AND c.id = t.categoria_id
        WHERE t.usuario_id = ? AND t.fecha_local = ? AND t.tipo = 'gasto'
          AND t.estado = 'confirmado' AND t.is_deleted = 0
        GROUP BY t.categoria_id, c.nombre, c.icono
        ORDER BY total DESC
        """,
        (user_id, date_value),
    ).fetchall()
    return dict_rows(rows)


def serialize_goal(conn, user_id, goal_id):
    row = conn.execute(
        "SELECT * FROM v_metas_estado WHERE usuario_id = ? AND meta_id = ?",
        (user_id, goal_id),
    ).fetchone()
    return dict(row) if row else None


def goal_plan(
    conn,
    user_id,
    as_of=None,
    meses=finance_engine.MESES_POR_DEFECTO,
    colchon_pct=finance_engine.COLCHON_PCT_POR_DEFECTO,
    income_override=None,
    expense_override=None,
    capacity_override=None,
    prioridades=None,
    incluir_metas=None,
    simulacion=False,
    overrides=None,
):
    """Calcula el plan de metas sin escribir en la base.

    Lee las metas desde `v_metas_progreso` y la capacidad desde
    `finance_engine`, y delega la optimizacion en `optimization`.
    """
    as_of = as_of or local_date()
    capacity = finance_engine.monthly_capacity(
        conn,
        user_id,
        as_of,
        meses=meses,
        colchon_pct=colchon_pct,
        income_override=income_override,
        expense_override=expense_override,
        capacity_override=capacity_override,
    )
    rows = conn.execute(
        """
        SELECT * FROM v_metas_progreso
        WHERE usuario_id = ?
        ORDER BY fecha_limite, meta_id
        """,
        (user_id,),
    ).fetchall()

    plan = optimization.plan_goals(
        [dict(row) for row in rows],
        capacity["capacidad_mensual"],
        as_of,
        horizon=meses,
        prioridades=prioridades,
        incluir_metas=incluir_metas,
        entradas=capacity["entradas"],
    )
    plan["simulacion"] = bool(simulacion)
    if simulacion:
        plan["overrides"] = overrides or {}
    return plan


def plan_resumen(conn, user_id, as_of=None):
    """Resumen compacto del plan para /home?incluir_plan=1."""
    plan = goal_plan(conn, user_id, as_of=as_of)
    mes_actual = plan["capacidad_mensual"][0] if plan["capacidad_mensual"] else {}
    metas = []
    for meta in plan["metas"]:
        asignacion = meta["asignacion_mensual"] or [0]
        metas.append(
            {
                "meta_id": meta["meta_id"],
                "nombre": meta["nombre"],
                "prioridad": meta["prioridad"],
                "asignacion_mes_actual": asignacion[0],
                "total_asignado": meta["total_asignado"],
                "cumplimiento": meta["cumplimiento"],
                "estado": meta["estado"],
                "mes_estimado_cumplimiento": meta["mes_estimado_cumplimiento"],
            }
        )
    return {
        "horizonte_meses": plan["horizonte_meses"],
        "factible": plan["factible"],
        "solver": plan["solver"],
        "confianza": plan["confianza"],
        "capacidad_mes_actual": mes_actual.get("capacidad", 0),
        "metas": metas,
        "resumen": plan["resumen"],
        "diagnostico": plan["diagnostico"],
    }
