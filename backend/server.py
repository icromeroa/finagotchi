import re
import sqlite3
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_NAME = "finagotchi.db"
PRESUPUESTO_DIARIO = 50000.0  # Límite por defecto en COP[cite: 3]


def init_sqlite():
    """Inicializa la base de datos SQLite creando las tablas si no existen."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            device_id TEXT,
            timestamp TEXT,
            transaction_type TEXT,
            amount REAL,
            category TEXT,
            raw_text TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS estado_mascota (
            id INTEGER PRIMARY KEY,
            salud INTEGER,
            animo TEXT
        )
    """
    )
    cursor.execute("SELECT COUNT(*) FROM estado_mascota")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO estado_mascota (id, salud, animo) VALUES (1, 100,"
            " 'feliz')"
        )
    conn.commit()
    conn.close()


def procesar_nlp_backend(texto: str) -> dict:
    """Extrae las variables financieras a partir del texto bruto procesado por voz."""
    texto_lower = texto.lower()

    # Detectar consulta de balance[cite: 1, 3]
    if any(
        p in texto_lower
        for p in [
            "cómo me fue",
            "como me fue",
            "balance",
            "resumen",
            "cuánto me queda",
        ]
    ):
        return {
            "transaction_type": "consulta_balance",
            "amount": 0.0,
            "category": "consultas",
        }

    # Extraer el primer número encontrado
    numeros = re.findall(r"\d+", texto_lower.replace(".", "").replace(",", ""))
    monto = float(numeros[0]) if numeros else 10000.0

    # Clasificar ingreso vs gasto[cite: 1, 3, 7]
    palabras_ingreso = [
        "pagaron",
        "ingresó",
        "ingreso",
        "recibí",
        "recibi",
        "gané",
        "gane",
        "cobré",
    ]
    if any(p in texto_lower for p in palabras_ingreso):
        return {
            "transaction_type": "income",
            "amount": monto,
            "category": "salary",
        }

    # Asignación de categorías de gasto[cite: 1, 3]
    categoria = "food" if any(p in texto_lower for p in ["almuerzo", "café", "comida"]) else "other"
    return {
        "transaction_type": "expense",
        "amount": monto,
        "category": categoria,
    }


@app.post("/api/v1/finagotchi/telemetry")
def receive_telemetry():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "Body JSON requerido"}), 400

    # Validación de contrato IoT[cite: 1, 2, 6]
    required_fields = ["message_id", "device_id", "timestamp", "sequence", "measurements"]
    if not all(field in data for field in required_fields):
        return (
            jsonify({
                "status": "error",
                "message": (
                    "Contrato inválido: faltan campos en el sobre común"
                ),
            }),
            400,
        )

    measurements = data["measurements"]
    raw_text = measurements.get("raw_voice_text", "")
    message_id = data["message_id"]
    device_id = data["device_id"]
    timestamp = data["timestamp"]

    # Inferencia semántica en Backend[cite: 1, 2]
    nlp_result = procesar_nlp_backend(raw_text)
    tipo = nlp_result["transaction_type"]
    monto = nlp_result["amount"]
    categoria = nlp_result["category"]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Obtener estado de la mascota[cite: 2, 3]
    cursor.execute("SELECT salud, animo FROM estado_mascota WHERE id = 1")
    salud, animo = cursor.fetchone()

    # Obtener acumulados
    cursor.execute("SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'income'")
    total_ingresos = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'expense'")
    total_gastos = cursor.fetchone()[0] or 0.0

    if tipo == "consulta_balance":
        balance_neto = total_ingresos - total_gastos
        conn.close()
        return (
            jsonify({
                "status": "success",
                "tipo": "consulta_balance",
                "total_ingresos": total_ingresos,
                "total_gastos": total_gastos,
                "balance_neto": balance_neto,
                "salud": salud,
                "animo": animo,
                "alerta_activa": salud < 20 or total_gastos > PRESUPUESTO_DIARIO,
            }),
            200,
        )

    # Actualizar estado de mascota y acumulados[cite: 3, 7]
    if tipo == "income":
        total_ingresos += monto
        salud = min(100, salud + 15)
        animo = "feliz"
    elif tipo == "expense":
        total_gastos += monto
        if total_gastos > PRESUPUESTO_DIARIO:
            salud = max(0, salud - 25)
            animo = "alerta" if salud < 30 else "triste"

    # Evaluación de Alertas críticas del proyecto[cite: 3, 7]
    alerta_activa = (total_gastos > PRESUPUESTO_DIARIO) or (salud < 20)

    # Persistencia en SQLite[cite: 1, 2]
    try:
        cursor.execute(
            """
            INSERT INTO transacciones (message_id, device_id, timestamp, transaction_type, amount, category, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (message_id, device_id, timestamp, tipo, monto, categoria, raw_text),
        )
        cursor.execute(
            "UPDATE estado_mascota SET salud = ?, animo = ? WHERE id = 1",
            (salud, animo),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"status": "error", "message": "message_id duplicado"}), 409
    finally:
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
            "alerta_activa": alerta_activa,
            "gastos_acumulados": total_gastos,
            "ingresos_acumulados": total_ingresos,
        }),
        201,
    )


if __name__ == "__main__":
    init_sqlite()
    print("🚀 SERVIDOR BACKEND FINAGOTCHI ESCUCHANDO (http://127.0.0.1:5000)")
    app.run(debug=True, port=5000)