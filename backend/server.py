import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from flask import Flask, jsonify, request

# 1. Asegurar la importación modular de la carpeta 'database'
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
from database.init_db import DB_PATH, init_sqlite

app = Flask(__name__)

# Regla de Negocio: Presupuesto diario máximo de gastos (en COP)
PRESUPUESTO_DIARIO = 30000.0


def calcular_estado_mascota(total_ingresos, total_gastos):
    """Calcula la salud y el ánimo de FinaGotchi según la ejecución presupuestal del día activo."""
    neto = total_ingresos - total_gastos
    salud = 100

    if total_gastos > PRESUPUESTO_DIARIO:
        exceso = total_gastos - PRESUPUESTO_DIARIO
        penalizacion = int((exceso / 5000.0) * 10)
        salud = max(0, 100 - penalizacion)
    elif neto < 0 and total_ingresos == 0 and total_gastos > 0:
        salud = max(20, 100 - int((total_gastos / PRESUPUESTO_DIARIO) * 50))

    if salud <= 20:
        animo = "ALERTA / CRÍTICO"
    elif salud <= 50:
        animo = "TRISTE"
    elif salud <= 80:
        animo = "PREOCUPADO"
    else:
        animo = "FELIZ"

    return salud, animo, neto


def procesar_nlp_backend(texto: str) -> dict:
    """Extrae intenciones, montos grandes corregidos y categorías dinámicas."""
    texto_lower = texto.lower()

    # 1. Distinguir Cierre de Día vs Consulta Intermedia
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

    # 2. LIMPIEZA DE MONTOS GRANDES (Atiende "50 000", "50.000", "$45,000")
    # Unifica dígitos separados por espacio (ej: "50 000" -> "50000")
    texto_limpio = re.sub(r"(\d+)\s+(\d+)", r"\1\2", texto_lower)
    # Remueve signos pesos, puntos y comas de miles
    texto_limpio = (
        texto_limpio.replace(".", "").replace(",", "").replace("$", "")
    )

    numeros = re.findall(r"\d+", texto_limpio)
    monto = float(numeros[0]) if numeros else 10000.0

    # Soporte para expresiones abreviadas como "50 mil" o "50k"
    if monto < 1000 and any(kw in texto_lower for kw in ["mil", "k"]):
        monto = monto * 1000.0

    # 3. Determinación de Tipo (Ingreso vs Gasto)
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
    ]
    es_ingreso = any(p in texto_lower for p in palabras_ingreso)
    tipo_transaccion = "income" if es_ingreso else "expense"

    # 4. Categorización Dinámica
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
        "salary": ["sueldo", "salario", "trabajo", "pago", "quincena"],
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


# ==========================================
# 📍 ENDPOINT DE TELEMETRÍA (Ruta Principal)
# ==========================================
@app.post("/api/v1/finagotchi/telemetry")
def receive_telemetry():
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify({"status": "error", "message": "Payload JSON requerido"}),
            400,
        )

    # Validar campos obligatorios de la envolvente de telemetría
    for required_field in ["message_id", "device_id", "timestamp"]:
        if required_field not in data:
            return (
                jsonify({
                    "status": "error",
                    "message": f"Campo requerido omitido: {required_field}",
                }),
                400,
            )

    measurements = data.get("measurements", {})
    raw_text = measurements.get("raw_voice_text", "")
    message_id = data["message_id"]
    device_id = data["device_id"]
    timestamp = data["timestamp"]

    nlp = procesar_nlp_backend(raw_text)
    tipo = nlp["transaction_type"]
    monto = nlp["amount"]
    categoria = nlp["category"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- CASO A: CONSULTA PARCIAL ("¿Cómo voy?") ---
    if tipo == "consulta_estado":
        cursor.execute(
            "SELECT SUM(amount) FROM transacciones WHERE transaction_type ="
            " 'income' AND cerrado = 0"
        )
        total_ingresos = cursor.fetchone()[0] or 0.0

        cursor.execute(
            "SELECT SUM(amount) FROM transacciones WHERE transaction_type ="
            " 'expense' AND cerrado = 0"
        )
        total_gastos = cursor.fetchone()[0] or 0.0

        salud, animo, neto = calcular_estado_mascota(
            total_ingresos, total_gastos
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
                "alerta_activa": salud < 20
                or total_gastos > PRESUPUESTO_DIARIO,
            }),
            200,
        )

    # --- CASO B: CIERRE DEFINITIVO DEL DÍA ("¿Cómo me fue el día de hoy?") ---
    if tipo == "cierre_dia":
        cursor.execute(
            "SELECT SUM(amount) FROM transacciones WHERE transaction_type ="
            " 'income' AND cerrado = 0"
        )
        total_ingresos = cursor.fetchone()[0] or 0.0

        cursor.execute(
            "SELECT SUM(amount) FROM transacciones WHERE transaction_type ="
            " 'expense' AND cerrado = 0"
        )
        total_gastos = cursor.fetchone()[0] or 0.0

        salud, animo, neto = calcular_estado_mascota(
            total_ingresos, total_gastos
        )

        # Marca las transacciones activas como cerradas
        cursor.execute("UPDATE transacciones SET cerrado = 1 WHERE cerrado = 0")
        cursor.execute(
            "UPDATE estado_mascota SET salud = 100, animo = 'FELIZ' WHERE id ="
            " 1"
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
                "salud": salud,
                "animo": animo,
                "alerta_activa": salud < 20
                or total_gastos > PRESUPUESTO_DIARIO,
            }),
            200,
        )

    # --- CASO C: REGISTRO DE NUEVA TRANSACCIÓN (Gasto o Ingreso) ---
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

    # Calcular acumulados de transacciones no cerradas (cerrado = 0)
    cursor.execute(
        "SELECT SUM(amount) FROM transacciones WHERE transaction_type ="
        " 'income' AND cerrado = 0"
    )
    total_ingresos = cursor.fetchone()[0] or 0.0

    cursor.execute(
        "SELECT SUM(amount) FROM transacciones WHERE transaction_type ="
        " 'expense' AND cerrado = 0"
    )
    total_gastos = cursor.fetchone()[0] or 0.0

    salud, animo, neto = calcular_estado_mascota(total_ingresos, total_gastos)

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
            "alerta_activa": total_gastos > PRESUPUESTO_DIARIO or salud < 20,
            "gastos_acumulados": total_gastos,
            "ingresos_acumulados": total_ingresos,
            "balance_neto": neto,
        }),
        201,
    )


# Ruta raíz para verificar que el servidor esté encendido
@app.get("/")
def index():
    return jsonify({
        "status": "online",
        "service": "Finagotchi Backend API",
        "endpoints": ["POST /api/v1/finagotchi/telemetry"],
    })


if __name__ == "__main__":
    init_sqlite()  # Verifica y crea la base de datos finagotchi.db
    print("=========================================================")
    print("🚀 SERVIDOR BACKEND FINAGOTCHI INICIADO")
    print("👉 Endpoint activo: POST /api/v1/finagotchi/telemetry")
    print("👉 Presupuesto diario máximo: $30,000 COP")
    print("=========================================================\n")
    app.run(debug=True, port=5000)