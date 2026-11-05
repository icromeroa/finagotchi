"""Motor de calculo financiero puro para FinaGotchi.

Todas las funciones reciben la fecha de corte `as_of` y no dependen de
`date('now')`. El modulo no escribe en la base: solo lee y devuelve
diccionarios serializables.

Uso principal:

    from backend.finance_engine import monthly_capacity

    capacidad = monthly_capacity(conn, usuario_id, "2026-11-05", meses=12)
"""

import calendar
from datetime import date as date_cls
from datetime import timedelta

DIAS_VENTANA_INGRESO = 90
COLCHON_PCT_POR_DEFECTO = 10.0
MESES_POR_DEFECTO = 12
MESES_MAXIMOS = 24


def parse_date(value):
    """Convierte texto ISO a `date`; devuelve None si no es valido."""
    try:
        return date_cls.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def first_day_of_month(value):
    moment = parse_date(value)
    if moment is None:
        return None
    return moment.replace(day=1)


def last_day_of_month(value):
    moment = parse_date(value)
    if moment is None:
        return None
    return moment.replace(day=calendar.monthrange(moment.year, moment.month)[1])


def days_in_month(value):
    moment = parse_date(value)
    if moment is None:
        return 0
    return calendar.monthrange(moment.year, moment.month)[1]


def month_key(value):
    moment = parse_date(value)
    if moment is None:
        return None
    return moment.strftime("%Y-%m")


def add_months(value, months):
    """Suma meses conservando el dia cuando es posible."""
    moment = parse_date(value)
    if moment is None:
        return None
    total = moment.month - 1 + int(months)
    year = moment.year + total // 12
    month = total % 12 + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


def months_until(deadline, as_of):
    """Meses completos disponibles entre `as_of` y `deadline`, inclusive.

    Devuelve 0 si el plazo ya paso o si la fecha no es valida.
    """
    limit = parse_date(deadline)
    today = parse_date(as_of)
    if limit is None or today is None:
        return 0
    if limit < today:
        return 0
    months = (limit.year - today.year) * 12 + (limit.month - today.month) + 1
    return max(0, months)


def _round_money(value):
    """Redondeo comercial a entero COP para valores no negativos."""
    return int(float(value) + 0.5)


def _clamp_pct(colchon_pct):
    try:
        pct = float(colchon_pct)
    except (TypeError, ValueError):
        pct = COLCHON_PCT_POR_DEFECTO
    return max(0.0, min(50.0, pct))


def declared_monthly_income(conn, user_id):
    """Ingreso mensual declarado en el perfil, o None si no hay dato util."""
    row = conn.execute(
        "SELECT ingreso_total_mensual FROM perfil_financiero WHERE usuario_id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    value = int(row["ingreso_total_mensual"] or 0)
    return value if value > 0 else None


def observed_monthly_income(conn, user_id, as_of, window_days=DIAS_VENTANA_INGRESO):
    """Promedio mensual observado de ingresos confirmados.

    Suma los ingresos de la ventana y los proyecta a 30 dias. Si no hay
    ingresos, devuelve None. Es deliberadamente conservador para periodos con
    pocos datos.
    """
    today = parse_date(as_of)
    if today is None:
        return None
    start = today - timedelta(days=max(1, int(window_days)) - 1)
    row = conn.execute(
        """
        SELECT COALESCE(SUM(monto), 0) AS total
        FROM transacciones
        WHERE usuario_id = ? AND tipo = 'ingreso' AND estado = 'confirmado'
          AND is_deleted = 0 AND fecha_local BETWEEN ? AND ?
        """,
        (user_id, start.isoformat(), today.isoformat()),
    ).fetchone()
    total = int(row["total"] or 0) if row else 0
    if total <= 0:
        return None
    return _round_money(total * 30.0 / max(1, int(window_days)))


def estimate_income(conn, user_id, as_of, override=None):
    """Estima el ingreso mensual con criterio conservador.

    Devuelve un diccionario con las fuentes, el valor usado y su origen.
    """
    declarado = declared_monthly_income(conn, user_id)
    observado = observed_monthly_income(conn, user_id, as_of)

    if override is not None:
        estimado = max(0, int(override))
        fuente = "simulacion"
    elif declarado is not None and observado is not None:
        estimado = min(declarado, observado)
        fuente = "minimo_declarado_observado"
    elif declarado is not None:
        estimado = declarado
        fuente = "declarado"
    elif observado is not None:
        estimado = observado
        fuente = "observado"
    else:
        estimado = 0
        fuente = "sin_datos"

    return {
        "ingreso_declarado": declarado,
        "ingreso_observado": observado,
        "ingreso_estimado": estimado,
        "fuente_ingreso": fuente,
    }


def _approved_monthly_expense(conn, user_id, month_start):
    row = conn.execute(
        """
        SELECT COALESCE(SUM(pc.monto_limite_mensual), 0) AS total
        FROM presupuesto_categoria pc
        JOIN presupuestos p
          ON p.usuario_id = pc.usuario_id AND p.id = pc.presupuesto_id
        WHERE pc.usuario_id = ? AND pc.tipo = 'gasto' AND p.aprobado = 1
          AND ? BETWEEN p.fecha_inicio AND p.fecha_fin
        """,
        (user_id, month_start),
    ).fetchone()
    return int(row["total"] or 0) if row else 0


def _daily_budget(conn, user_id, as_of):
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
        (user_id, as_of, user_id),
    ).fetchone()
    return int(row["monto"] or 0) if row else 0


def planned_monthly_expense(conn, user_id, as_of, override=None):
    """Gasto mensual planificado y su fuente.

    Prioriza el presupuesto mensual aprobado para no sumar dos veces el
    presupuesto diario y los limites por categoria. Si no existe, usa el
    presupuesto diario vigente multiplicado por los dias del mes.
    """
    today = parse_date(as_of)
    if today is None:
        return {"gasto_planificado_mensual": 0, "fuente_presupuesto": "sin_datos"}

    if override is not None:
        return {
            "gasto_planificado_mensual": max(0, int(override)),
            "fuente_presupuesto": "simulacion",
        }

    month_start = today.replace(day=1).isoformat()
    aprobado = _approved_monthly_expense(conn, user_id, month_start)
    if aprobado > 0:
        return {
            "gasto_planificado_mensual": aprobado,
            "fuente_presupuesto": "presupuesto_mensual",
        }

    diario = _daily_budget(conn, user_id, today.isoformat())
    if diario > 0:
        return {
            "gasto_planificado_mensual": diario * days_in_month(today),
            "fuente_presupuesto": "presupuesto_diario",
        }

    return {"gasto_planificado_mensual": 0, "fuente_presupuesto": "sin_datos"}


def liquidity_cushion(income, colchon_pct=COLCHON_PCT_POR_DEFECTO):
    """Colchon de liquidez sobre el ingreso estimado."""
    return _round_money(max(0, int(income)) * _clamp_pct(colchon_pct) / 100.0)


def monthly_capacity(
    conn,
    user_id,
    as_of,
    meses=MESES_POR_DEFECTO,
    colchon_pct=COLCHON_PCT_POR_DEFECTO,
    income_override=None,
    expense_override=None,
    capacity_override=None,
):
    """Capacidad mensual de ahorro para el horizonte solicitado.

    El primer mes se prorratea por los dias restantes. Los meses posteriores
    usan el mes completo. Si `capacity_override` viene informado, se usa tal
    cual en todos los meses.
    """
    today = parse_date(as_of)
    if today is None:
        raise ValueError("fecha_invalida")
    meses = max(1, min(MESES_MAXIMOS, int(meses)))

    ingreso = estimate_income(conn, user_id, as_of, override=income_override)
    gasto = planned_monthly_expense(conn, user_id, as_of, override=expense_override)
    ingreso_mensual = ingreso["ingreso_estimado"]
    gasto_mensual = gasto["gasto_planificado_mensual"]
    pct = _clamp_pct(colchon_pct)

    resultado = []
    for indice in range(1, meses + 1):
        month_date = add_months(today.replace(day=1), indice - 1)
        total_dias = days_in_month(month_date)

        if indice == 1:
            dias_disponibles = total_dias - today.day + 1
        else:
            dias_disponibles = total_dias
        fraccion = dias_disponibles / float(total_dias) if total_dias else 0.0

        ingreso_mes = _round_money(ingreso_mensual * fraccion)
        gasto_mes = _round_money(gasto_mensual * fraccion)
        colchon_mes = liquidity_cushion(ingreso_mes, pct)

        if capacity_override is not None:
            capacidad = max(0, int(capacity_override))
        else:
            capacidad = max(0, ingreso_mes - gasto_mes - colchon_mes)

        resultado.append(
            {
                "indice": indice,
                "mes": month_date.strftime("%Y-%m"),
                "dias_mes": total_dias,
                "dias_disponibles": dias_disponibles,
                "ingreso_estimado": ingreso_mes,
                "gasto_planificado": gasto_mes,
                "colchon": colchon_mes,
                "capacidad": capacidad,
            }
        )

    return {
        "as_of": today.isoformat(),
        "horizonte_meses": meses,
        "entradas": {
            "ingreso_declarado": ingreso["ingreso_declarado"],
            "ingreso_observado": ingreso["ingreso_observado"],
            "ingreso_estimado": ingreso_mensual,
            "gasto_planificado_mensual": gasto_mensual,
            "colchon_pct": pct,
            "colchon_mensual": liquidity_cushion(ingreso_mensual, pct),
            "fuente_ingreso": ingreso["fuente_ingreso"],
            "fuente_presupuesto": gasto["fuente_presupuesto"],
        },
        "capacidad_mensual": resultado,
    }


def summarize_capacity(capacidad_mensual):
    """Total y minimo de capacidad para resumenes y diagnosticos."""
    valores = [int(mes["capacidad"]) for mes in capacidad_mensual]
    return {
        "capacidad_total": sum(valores),
        "capacidad_minima": min(valores) if valores else 0,
    }
