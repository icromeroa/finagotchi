import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from flask import Flask, jsonify, request

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
from database.init_db import DB_PATH, init_sqlite

app = Flask(__name__)


def obtener_presupuestos_y_saldos(cursor):
    """Calcula el estado actual de cada categoría y sus cupos restantes."""
    cursor.execute("SELECT categoria, monto_limite FROM presupuestos_categoria")
    presupuestos = dict(cursor.fetchall())

    cursor.execute(
        "SELECT category, SUM(amount) FROM transacciones WHERE transaction_type = 'expense' AND cerrado = 0 GROUP BY category"
    )
    gastos_por_cat = dict(cursor.fetchall())

    desglose = {}
    exceso_total_categorias = 0.0

    for cat, limite in presupuestos.items():
        gastado = gastos_por_cat.get(cat, 0.0)
        restante = limite - gastado
        desglose[cat] = {
            "limite": limite,
            "gastado": gastado,
            "restante": restante,
            "superado": gastado > limite,
        }
        if gastado > limite:
            exceso_total_categorias += gastado - limite

    return desglose, exceso_total_categorias


def calcular_salud_y_animo(
    salud_actual, total_ingresos, total_gastos, exceso_categorias
):
    """Calcula la salud considerando el balance neto y los excesos por categoría."""
    neto = total_ingresos - total_gastos
    nueva_salud = salud_actual

    # Penalización si hay categorías excedidas
    if exceso_categorias > 0:
        penalizacion = int((exceso_categorias / 5000.0) * 8)
        nueva_salud -= penalizacion

    # Bonificación si el balance neto del día es altamente positivo
    if neto > 0 and exceso_categorias == 0:
        recuperacion = int((neto / 10000.0) * 5)
        nueva_salud += recuperacion

    nueva_salud = max(0, min(100, nueva_salud))

    if nueva_salud <= 20:
        animo = "ALERTA / CRÍTICO"
    elif nueva_salud <= 50:
        animo = "TRISTE"
    elif nueva_salud <= 80:
        animo = "PREOCUPADO"
    else:
        animo = "FELIZ"

    return nueva_salud, animo, neto


def procesar_nlp_backend(texto: str) -> dict:
    texto_lower = texto.lower()

    if any(
        p in texto_lower
        for p in [
            "cómo me fue",
            "como me fue",
            "cerrar día",
            "cerrar dia",
            "terminar día",
        ]
    ):
        return {
            "transaction_type": "cierre_dia",
            "amount": 0.0,
            "category": "consultas",
        }

    if any(
        p in texto_lower
        for p in [
            "cómo voy",
            "como voy",
            "cómo me está yendo",
            "como me esta yendo",
            "resumen",
            "balance",
        ]
    ):
        return {
            "transaction_type": "consulta_estado",
            "amount": 0.0,
            "category": "consultas",
        }

    # Limpieza mejorada para captura de números simples o compuestos ("pagaron 50000", "50 000")
    texto_limpio = re.sub(r"(\d+)\s+(\d+)", r"\1\2", texto_lower)
    texto_limpio = (
        texto_limpio.replace(".", "").replace(",", "").replace("$", "")
    )

    numeros = re.findall(r"\d+", texto_limpio)
    monto = float(numeros[0]) if numeros else 10000.0

    if monto < 1000 and any(kw in texto_lower for kw in ["mil", "k"]):
        monto = monto * 1000.0

    palabras_ingreso = [
        "pagaron",
        "ingresó",
        "ingreso",
        "recibí",
        "recibi",
        "gané",
        "gane",
        "cobré",
        "sueldo",
        "salario",
        "pago",
    ]
    es_ingreso = any(p in texto_lower for p in palabras_ingreso)
    tipo_transaccion = "income" if es_ingreso else "expense"

    reglas_categoria = {
        "food": [
            "almuerzo",
            "desayuno",
            "cena",
            "comida",
            "restaurante",
            "café",
            "cafe",
            "empanada",
        ],
        "transport": [
            "transporte",
            "pasaje",
            "bus",
            "transmilenio",
            "uber",
            "taxi",
            "viaje",
            "gasolina",
        ],
        "entertainment": [
            "cine",
            "fiesta",
            "bar",
            "cerveza",
            "juego",
            "salida",
            "concierto",
        ],
        "health": ["farmacia", "drogueria", "medicina", "medico", "salud"],
        "housing": [
            "arriendo",
            "alquiler",
            "servicios",
            "luz",
            "agua",
            "gas",
            "internet",
        ],
        "salary": [
            "sueldo",
            "salario",
            "trabajo",
            "quincena",
            "pagaron",
            "pago",
        ],
    }

    cat_detectada = None
    for cat, palabras in reglas_categoria.items():
        if any(w in texto_lower for w in palabras):
            cat_detectada = cat
            break

    if not cat_detectada:
        cat_detectada = "salary" if es_ingreso else "other"

    return {
        "transaction_type": tipo_transaccion,
        "amount": monto,
        "category": cat_detectada,
    }


@app.post("/api/v1/finagotchi/telemetry")
def receive_telemetry():
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify({"status": "error", "message": "Payload JSON requerido"}),
            400,
        )

    message_id = data.get("message_id")
    device_id = data.get("device_id")
    timestamp = data.get("timestamp")
    raw_text = data.get("measurements", {}).get("raw_voice_text", "")

    nlp = procesar_nlp_backend(raw_text)
    tipo = nlp["transaction_type"]
    monto = nlp["amount"]
    categoria = nlp["category"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener Salud actual acumulada
    cursor.execute("SELECT salud FROM estado_mascota WHERE id = 1")
    salud_actual = cursor.fetchone()[0]

    # --- CASO A: CONSULTA DE ESTADO ("¿Cómo voy?") ---
    if tipo == "consulta_estado":
        cursor.execute(
            "SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'income' AND cerrado = 0"
        )
        total_ingresos = cursor.fetchone()[0] or 0.0

        cursor.execute(
            "SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'expense' AND cerrado = 0"
        )
        total_gastos = cursor.fetchone()[0] or 0.0

        desglose, exceso_total = obtener_presupuestos_y_saldos(cursor)
        salud, animo, neto = calcular_salud_y_animo(
            salud_actual, total_ingresos, total_gastos, exceso_total
        )
        conn.close()

        return (
            jsonify({
                "status": "success",
                "tipo": "consulta_estado",
                "total_ingresos": total_ingresos,
                "total_gastos": total_gastos,
                "balance_neto": neto,
                "salud": salud,
                "animo": animo,
                "categorias": desglose,
            }),
            200,
        )

    # --- CASO B: CIERRE DEL DÍA ("¿Cómo me fue el día de hoy?") ---
    if tipo == "cierre_dia":
        cursor.execute(
            "SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'income' AND cerrado = 0"
        )
        total_ingresos = cursor.fetchone()[0] or 0.0

        cursor.execute(
            "SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'expense' AND cerrado = 0"
        )
        total_gastos = cursor.fetchone()[0] or 0.0

        desglose, exceso_total = obtener_presupuestos_y_saldos(cursor)
        salud_final, animo_final, neto = calcular_salud_y_animo(
            salud_actual, total_ingresos, total_gastos, exceso_total
        )

        # Cierra las transacciones pero RETIENE la salud alcanzada para el día siguiente
        cursor.execute("UPDATE transacciones SET cerrado = 1 WHERE cerrado = 0")
        cursor.execute(
            "UPDATE estado_mascota SET salud = ?, animo = ? WHERE id = 1",
            (salud_final, animo_final),
        )
        conn.commit()
        conn.close()

        return (
            jsonify({
                "status": "success",
                "tipo": "cierre_dia",
                "total_ingresos": total_ingresos,
                "total_gastos": total_gastos,
                "balance_neto": neto,
                "salud_heredada": salud_final,
                "animo": animo_final,
                "categorias": desglose,
            }),
            200,
        )

    # --- CASO C: NUEVA TRANSACCIÓN ---
    try:
        cursor.execute(
            """
            INSERT INTO transacciones (message_id, device_id, timestamp, transaction_type, amount, category, raw_text, cerrado)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (message_id, device_id, timestamp, tipo, monto, categoria, raw_text),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return (
            jsonify({
                "status": "error",
                "message": "Conflict: message_id duplicado",
            }),
            409,
        )

    cursor.execute(
        "SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'income' AND cerrado = 0"
    )
    total_ingresos = cursor.fetchone()[0] or 0.0

    cursor.execute(
        "SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'expense' AND cerrado = 0"
    )
    total_gastos = cursor.fetchone()[0] or 0.0

    desglose, exceso_total = obtener_presupuestos_y_saldos(cursor)
    salud, animo, neto = calcular_salud_y_animo(
        salud_actual, total_ingresos, total_gastos, exceso_total
    )

    cursor.execute(
        "UPDATE estado_mascota SET salud = ?, animo = ? WHERE id = 1",
        (salud, animo),
    )
    conn.commit()
    conn.close()

    return (
        jsonify({
            "status": "success",
            "message_id": message_id,
            "monto": monto,
            "transaction_type": tipo,
            "category": categoria,
            "salud": salud,
            "animo": animo,
            "gastos_acumulados": total_gastos,
            "ingresos_acumulados": total_ingresos,
            "balance_neto": neto,
            "categorias": desglose,
        }),
        201,
    )


if __name__ == "__main__":
    init_sqlite()
    app.run(debug=True, port=5000)