"""Optimizacion de metas de ahorro con programacion lineal.

El modelo maximiza el cumplimiento ponderado por prioridad sujeto a la
capacidad mensual y a las fechas limite. Solo propone: no escribe en la base.

    from backend.optimization import plan_goals
    plan = plan_goals(metas, capacidad, as_of="2026-11-05")
"""

import math

from . import finance_engine as fe

EPSILON = 1e-6
PRIORIDAD_MIN = 1
PRIORIDAD_MAX = 5
ESTADO_COMPLETADA = "completada"
ESTADO_PARCIAL = "parcial"
ESTADO_SIN_ASIGNACION = "sin_asignacion"


def _clamp_priority(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return PRIORIDAD_MIN
    return max(PRIORIDAD_MIN, min(PRIORIDAD_MAX, number))


def _normalize_goal(goal):
    """Convierte una fila de SQLite o un diccionario en una meta homogenea."""
    data = dict(goal)
    ahorrado = data.get("ahorrado")
    if ahorrado is None:
        ahorrado = data.get("ahorrado_actual", 0)
    return {
        "meta_id": int(data.get("meta_id") or data.get("id")),
        "nombre": str(data.get("nombre") or "Meta"),
        "monto_meta": max(0, int(data.get("monto_meta") or 0)),
        "ahorrado": max(0, int(ahorrado or 0)),
        "fecha_limite": str(data.get("fecha_limite") or ""),
        "prioridad": _clamp_priority(data.get("prioridad", PRIORIDAD_MIN)),
    }


def _prepare_goals(goals, as_of, horizon, prioridades=None, incluir_metas=None):
    prioridades = prioridades or {}
    incluir = None
    if incluir_metas is not None:
        incluir = {int(value) for value in incluir_metas}

    preparadas = []
    for goal in goals:
        normal = _normalize_goal(goal)
        if incluir is not None and normal["meta_id"] not in incluir:
            continue
        override = prioridades.get(normal["meta_id"])
        if override is None:
            override = prioridades.get(str(normal["meta_id"]))
        if override is not None:
            normal["prioridad"] = _clamp_priority(override)

        restante = max(0, normal["monto_meta"] - normal["ahorrado"])
        plazo = min(fe.months_until(normal["fecha_limite"], as_of), horizon)
        normal["restante"] = restante
        normal["meses_disponibles"] = plazo
        normal["planificable"] = restante > 0 and plazo > 0
        preparadas.append(normal)

    preparadas.sort(key=lambda item: item["meta_id"])
    return preparadas


def _capacity_values(capacity_data, horizon):
    values = [max(0, int(mes["capacidad"])) for mes in capacity_data]
    if len(values) < horizon:
        values.extend([0] * (horizon - len(values)))
    return values[:horizon]


def _build_problem(goals, capacidades, horizon):
    """Construye indices, restricciones y cotas del LP."""
    variables = []
    for goal in goals:
        if not goal["planificable"]:
            continue
        indices = []
        for mes in range(1, goal["meses_disponibles"] + 1):
            indices.append((mes, len(variables)))
            variables.append(("x", goal, mes))
        goal["_x"] = indices
        goal["_y"] = len(variables)
        variables.append(("y", goal, 0))

    total = len(variables)
    if total == 0:
        return None

    filas = []
    limite = []
    for mes in range(1, horizon + 1):
        fila = [0.0] * total
        for indice, (tipo, _, mes_variable) in enumerate(variables):
            if tipo == "x" and mes_variable == mes:
                fila[indice] = 1.0
        filas.append(fila)
        limite.append(float(capacidades[mes - 1]))

    for goal in goals:
        if not goal["planificable"]:
            continue
        fila = [0.0] * total
        for mes, indice in goal["_x"]:
            fila[indice] = -1.0
        fila[goal["_y"]] = float(goal["monto_meta"])
        filas.append(fila)
        limite.append(float(goal["ahorrado"]))

        fila = [0.0] * total
        for _, indice in goal["_x"]:
            fila[indice] = 1.0
        filas.append(fila)
        limite.append(float(goal["restante"]))

    bounds = []
    for tipo, _, _ in variables:
        if tipo == "x":
            bounds.append((0.0, None))
        else:
            bounds.append((0.0, 1.0))

    return {
        "variables": variables,
        "total": total,
        "horizon": horizon,
        "A_ub": filas,
        "b_ub": limite,
        "bounds": bounds,
    }


def _solve_linprog(problem):
    """Resuelve el LP en dos etapas: cumplimiento y luego anticipacion."""
    try:
        import numpy as np
        from scipy.optimize import linprog
    except Exception:  # noqa: BLE001 - sin SciPy se usa el fallback
        return None

    total = problem["total"]
    A = np.array(problem["A_ub"], dtype=float)
    b = np.array(problem["b_ub"], dtype=float)
    bounds = problem["bounds"]

    c_primary = np.zeros(total, dtype=float)
    for indice, (tipo, goal, _) in enumerate(problem["variables"]):
        if tipo == "y":
            c_primary[indice] = -float(goal["prioridad"])

    primary = linprog(c_primary, A_ub=A, b_ub=b, bounds=bounds, method="highs")
    if not primary.success:
        return None

    objetivo = -float(primary.fun)
    c_secondary = np.zeros(total, dtype=float)
    horizon = max(1, int(problem.get("horizon") or 1))
    for indice, (tipo, _, mes) in enumerate(problem["variables"]):
        if tipo == "x":
            c_secondary[indice] = mes / float(horizon)

    fila = np.zeros(total, dtype=float)
    for indice, (tipo, goal, _) in enumerate(problem["variables"]):
        if tipo == "y":
            fila[indice] = -float(goal["prioridad"])
    A2 = np.vstack([A, fila])
    b2 = np.append(b, -(objetivo - EPSILON))

    secondary = linprog(c_secondary, A_ub=A2, b_ub=b2, bounds=bounds, method="highs")
    resultado = secondary if secondary.success else primary

    asignaciones = {}
    for indice, (tipo, goal, mes) in enumerate(problem["variables"]):
        if tipo != "x":
            continue
        valor = max(0.0, float(resultado.x[indice]))
        asignaciones.setdefault(goal["meta_id"], {})[mes] = valor
    return asignaciones


def _greedy_plan(goals, capacidades, horizon):
    """Fallback determinista: prioridad descendente y plazo ascendente."""
    restante_capacidad = list(capacidades)
    asignaciones = {}
    orden = sorted(
        (goal for goal in goals if goal["planificable"]),
        key=lambda item: (-item["prioridad"], item["fecha_limite"], item["meta_id"]),
    )
    for goal in orden:
        pendiente = goal["restante"]
        fila = [0] * horizon
        for mes in range(1, goal["meses_disponibles"] + 1):
            if pendiente <= 0:
                break
            cupo = max(0, restante_capacidad[mes - 1])
            monto = min(pendiente, cupo)
            if monto > 0:
                fila[mes - 1] = monto
                restante_capacidad[mes - 1] -= monto
                pendiente -= monto
        asignaciones[goal["meta_id"]] = fila
    return asignaciones


def _round_plan(raw, goals, capacidades, horizon):
    """Convierte asignaciones flotantes en enteros sin exceder la capacidad."""
    pisos = {}
    for goal in goals:
        fila = [0] * horizon
        if goal["planificable"]:
            valores = raw.get(goal["meta_id"], {})
            for mes, valor in valores.items():
                if 1 <= mes <= horizon:
                    fila[mes - 1] = int(math.floor(max(0.0, valor) + 1e-9))
        pisos[goal["meta_id"]] = fila

    for goal in goals:
        fila = pisos[goal["meta_id"]]
        exceso = sum(fila) - goal["restante"]
        for mes in range(horizon - 1, -1, -1):
            if exceso <= 0:
                break
            recorte = min(fila[mes], exceso)
            fila[mes] -= recorte
            exceso -= recorte

    candidatos = []
    for goal in goals:
        if not goal["planificable"]:
            continue
        valores = raw.get(goal["meta_id"], {})
        for mes, valor in valores.items():
            if not (1 <= mes <= horizon):
                continue
            fraccion = max(0.0, valor) - math.floor(max(0.0, valor) + 1e-9)
            if fraccion > 1e-9:
                candidatos.append((fraccion, goal, mes))
    candidatos.sort(key=lambda item: (-item[0], item[1]["meta_id"], item[2]))

    for _, goal, mes in candidatos:
        fila = pisos[goal["meta_id"]]
        usados = sum(pisos[g["meta_id"]][mes - 1] for g in goals)
        if usados >= capacidades[mes - 1]:
            continue
        if sum(fila) >= goal["restante"]:
            continue
        fila[mes - 1] += 1

    return pisos


def _goal_result(goal, fila, horizon):
    total = sum(fila)
    saldo = goal["ahorrado"] + total
    monto = goal["monto_meta"]
    if monto <= 0:
        cumplimiento = 1.0
    else:
        cumplimiento = min(1.0, saldo / float(monto))
    faltante = max(0, monto - saldo)

    mes_cumplimiento = None
    if monto > 0 and saldo >= monto:
        acumulado = goal["ahorrado"]
        if acumulado >= monto:
            mes_cumplimiento = 0
        else:
            for mes, asignado in enumerate(fila, start=1):
                acumulado += asignado
                if acumulado >= monto:
                    mes_cumplimiento = mes
                    break

    if saldo >= monto:
        estado = ESTADO_COMPLETADA
    elif total > 0:
        estado = ESTADO_PARCIAL
    else:
        estado = ESTADO_SIN_ASIGNACION

    return {
        "meta_id": goal["meta_id"],
        "nombre": goal["nombre"],
        "prioridad": goal["prioridad"],
        "monto_meta": monto,
        "ahorrado_actual": goal["ahorrado"],
        "faltante_inicial": goal["restante"],
        "fecha_limite": goal["fecha_limite"],
        "meses_disponibles": goal["meses_disponibles"],
        "asignacion_mensual": list(fila[:horizon]) + [0] * max(0, horizon - len(fila)),
        "total_asignado": total,
        "saldo_proyectado": saldo,
        "cumplimiento": round(cumplimiento, 4),
        "faltante_proyectado": faltante,
        "mes_estimado_cumplimiento": mes_cumplimiento,
        "estado": estado,
    }


def _diagnostico(metas, entradas, capacidad_total, ponderado):
    pendientes = [
        meta for meta in metas if meta["estado"] != ESTADO_COMPLETADA
    ]
    if not metas:
        return {
            "nivel": "info",
            "codigo": "SIN_METAS",
            "mensaje": "No hay metas activas para planificar.",
            "recomendaciones": ["Crea una meta para recibir un plan de ahorro."],
        }
    if int(entradas.get("ingreso_estimado") or 0) <= 0:
        return {
            "nivel": "advertencia",
            "codigo": "PERFIL_INCOMPLETO",
            "mensaje": "No hay ingreso declarado ni observado suficiente.",
            "recomendaciones": [
                "Completa tu perfil financiero o registra ingresos confirmados."
            ],
        }
    if capacidad_total <= 0:
        return {
            "nivel": "advertencia",
            "codigo": "SIN_CAPACIDAD",
            "mensaje": "El ingreso cubre el gasto planificado y el colchon.",
            "recomendaciones": [
                "Reduce gastos variables o aumenta el ingreso para liberar capacidad."
            ],
        }
    if not pendientes:
        return {
            "nivel": "exito",
            "codigo": "METAS_ALCANZABLES",
            "mensaje": "Todas las metas se cumplen dentro del horizonte.",
            "recomendaciones": ["Mantiene el plan de ahorro propuesto."],
        }
    return {
        "nivel": "info",
        "codigo": "CAPACIDAD_LIMITADA",
        "mensaje": "La capacidad alcanza para el {0:.0f} % del plan ponderado.".format(
            ponderado * 100
        ),
        "recomendaciones": [
            "Prioriza la meta de mayor prioridad o reduce gastos variables.",
            "Ajusta la fecha limite o el monto de las metas menos prioritarias.",
        ],
    }


def _month_output(capacity_data, capacidades, indice):
    """Conserva el detalle del mes y fija la capacidad usada por el plan."""
    detalle = dict(capacity_data[indice]) if indice < len(capacity_data) else {}
    detalle["indice"] = indice + 1
    detalle.setdefault("mes", None)
    detalle["capacidad"] = capacidades[indice]
    return detalle


def _confianza(entradas):
    if int(entradas.get("ingreso_estimado") or 0) <= 0:
        return "baja"
    fuente = entradas.get("fuente_ingreso")
    presupuesto = entradas.get("fuente_presupuesto")
    if presupuesto == "sin_datos":
        return "baja"
    if fuente == "minimo_declarado_observado" and presupuesto == "presupuesto_mensual":
        return "alta"
    return "media"


def plan_goals(
    goals,
    capacity_data,
    as_of,
    horizon=None,
    prioridades=None,
    incluir_metas=None,
    entradas=None,
):
    """Calcula el plan de ahorro optimo y su diagnostico.

    `capacity_data` es la lista `capacidad_mensual` de
    `finance_engine.monthly_capacity`.
    """
    capacidades_completas = [max(0, int(mes["capacidad"])) for mes in capacity_data]
    horizonte = int(horizon or len(capacidades_completas) or 1)
    horizonte = max(1, min(fe.MESES_MAXIMOS, horizonte))
    capacidades = _capacity_values(capacity_data, horizonte)
    metas = _prepare_goals(
        goals,
        as_of,
        horizonte,
        prioridades=prioridades,
        incluir_metas=incluir_metas,
    )

    solver = "greedy"
    if any(goal["planificable"] for goal in metas):
        problem = _build_problem(metas, capacidades, horizonte)
        raw = _solve_linprog(problem) if problem else None
        if raw is not None:
            solver = "highs"
            filas = _round_plan(raw, metas, capacidades, horizonte)
        else:
            filas = _greedy_plan(metas, capacidades, horizonte)
    else:
        filas = {goal["meta_id"]: [0] * horizonte for goal in metas}

    resultados = [
        _goal_result(goal, filas.get(goal["meta_id"], [0] * horizonte), horizonte)
        for goal in metas
    ]

    peso_total = sum(meta["prioridad"] for meta in resultados)
    ponderado = (
        sum(meta["prioridad"] * meta["cumplimiento"] for meta in resultados)
        / float(peso_total)
        if peso_total
        else 0.0
    )
    capacidad_total = sum(capacidades)
    total_asignado = sum(meta["total_asignado"] for meta in resultados)

    restricciones = []
    for mes in range(1, horizonte + 1):
        usado = sum(meta["asignacion_mensual"][mes - 1] for meta in resultados)
        if capacidades[mes - 1] > 0 and usado >= capacidades[mes - 1]:
            restricciones.append("capacidad_mes_{0}".format(mes))
    for goal in metas:
        if not goal["planificable"]:
            continue
        fila = filas.get(goal["meta_id"], [])
        if sum(fila) > 0 and goal["meses_disponibles"] < horizonte:
            restricciones.append("plazo_meta_{0}".format(goal["meta_id"]))

    entradas = dict(entradas or {})
    if not entradas:
        entradas = {
            "ingreso_estimado": 0,
            "fuente_ingreso": "sin_datos",
            "fuente_presupuesto": "sin_datos",
        }

    return {
        "as_of": as_of,
        "horizonte_meses": horizonte,
        "moneda": "COP",
        "factible": True,
        "solver": solver,
        "confianza": _confianza(entradas),
        "entradas": entradas,
        "capacidad_mensual": [
            _month_output(capacity_data, capacidades, indice)
            for indice in range(horizonte)
        ],
        "metas": resultados,
        "resumen": {
            "capacidad_total": capacidad_total,
            "total_asignado": total_asignado,
            "metas_totales": len(resultados),
            "metas_completadas": sum(
                1 for meta in resultados if meta["estado"] == ESTADO_COMPLETADA
            ),
            "metas_parciales": sum(
                1 for meta in resultados if meta["estado"] == ESTADO_PARCIAL
            ),
            "metas_sin_asignacion": sum(
                1 for meta in resultados if meta["estado"] == ESTADO_SIN_ASIGNACION
            ),
            "cumplimiento_ponderado": round(ponderado, 4),
        },
        "restricciones_activas": restricciones,
        "diagnostico": _diagnostico(
            resultados, entradas, capacidad_total, ponderado
        ),
    }
