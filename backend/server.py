import re
import sqlite3
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_NAME = "finagotchi.db"

# Regla de Negocio: Presupuesto diario máximo de gastos (en COP)
PRESUPUESTO_DIARIO = 30000.0


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
            "INSERT INTO estado_mascota (id, salud, animo) VALUES (1, 100, 'FELIZ')"
        )
    conn.commit()
    conn.close()


def calcular_estado_mascota(total_ingresos, total_gastos):
    """Calcula la salud y el ánimo de la mascota según las finanzas acumuladas del día."""
    neto = total_ingresos - total_gastos
    salud = 100

    # 1. Si los gastos superan el presupuesto diario, penalizar proporcionalmente
    if total_gastos > PRESUPUESTO_DIARIO:
        exceso = total_gastos - PRESUPUESTO_DIARIO
        # Resta 10% de salud por cada $5.000 COP sobrepasados
        penalizacion = int((exceso / 5000.0) * 10)
        salud = max(0, 100 - penalizacion)

    # 2. Si hay saldo neto negativo sin haber registrado ingresos
    elif neto < 0 and total_ingresos == 0:
        salud = max(20, 100 - int((total_gastos / PRESUPUESTO_DIARIO) * 50))

    # 3. Definir estado de ánimo según la salud resultante
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
    """
    Inferencia de texto: detecta tipo de movimiento, monto y categoría 
    dinámicamente según las palabras clave de la frase.
    """
    texto_lower = texto.lower()

    # 1. Detectar si es una consulta de balance general
    if any(p in texto_lower for p in ["cómo me fue", "como me fue", "balance", "resumen", "cuánto me queda", "cuanto me queda"]):
        return {
            "transaction_type": "consulta_balance",
            "amount": 0.0,
            "category": "consultas"
        }

    # 2. Extraer el primer número mencionado en el texto (Monto)
    numeros = re.findall(r'\d+', texto_lower.replace('.', '').replace(',', ''))
    monto = float(numeros[0]) if numeros else 10000.0

    # Soporte para expresiones como "45 mil" o "45k"
    if monto < 100 and any(kw in texto_lower for kw in ["mil", "k"]):
        monto = monto * 1000.0

    # 3. Clasificar tipo de transacción (Ingreso vs Gasto)
    palabras_ingreso = ["pagaron", "ingresó", "ingreso", "recibí", "recibi", "gané", "gane", "cobré", "sueldo", "salario"]
    es_ingreso = any(p in texto_lower for p in palabras_ingreso)
    tipo_transaccion = "income" if es_ingreso else "expense"

    # 4. DETECCIÓN DINÁMICA DE CATEGORÍA BASADA EN LA FRASE
    
    # Diccionario de reglas por palabras clave
    reglas_categoria = {
        "food": [
            "almuerzo", "desayuno", "cena", "comida", "restaurante", "café", "cafe", 
            "helado", "hamburguesa", "pizza", "empanada", "pan", "mercado", "supermercado"
        ],
        "transport": [
            "transporte", "pasaje", "bus", "transmilenio", "uber", "taxi", "didi", 
            "cabify", "gasolina", "peaje", "moto", "carro"
        ],
        "entertainment": [
            "cine", "película", "salida", "fiesta", "bar", "cerveza", "juego", 
            "videojuego", "concierto", "evento", "ocio"
        ],
        "health": [
            "farmacia", "drogueria", "droguería", "remedio", "medicina", "médico", 
            "medico", "doctor", "cita medica", "salud"
        ],
        "education": [
            "libro", "fotocopia", "universidad", "pensión", "pension", "curso", 
            "matrícula", "matricula", "útiles", "utiles"
        ],
        "housing": [
            "arriendo", "alquiler", "servicios", "luz", "agua", "gas", "internet", "wifi"
        ],
        "salary": [
            "sueldo", "salario", "pago", "quincena", "mesada", "honorarios", "trabajo"
        ]
    }

    # Buscar coincidencia en la frase
    categoria_detectada = None
    for cat, palabras in reglas_categoria.items():
        if any(palabra in texto_lower for palabra in palabras):
            categoria_detectada = cat
            break

    # Si no coincide con ninguna palabra clave, asigna la categoría general
    if not categoria_detectada:
        categoria_detectada = "salary" if es_ingreso else "other"

    return {
        "transaction_type": tipo_transaccion,
        "amount": monto,
        "category": categoria_detectada
    }


@app.post("/api/v1/finagotchi/telemetry")
def receive_telemetry():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "Body JSON requerido"}), 400

    # Validar sobre IoT de telemetría
    required_fields = ["message_id", "device_id", "timestamp", "sequence", "measurements"]
    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Contrato JSON incompleto"}), 400

    measurements = data["measurements"]
    raw_text = measurements.get("raw_voice_text", "")
    message_id = data["message_id"]
    device_id = data["device_id"]
    timestamp = data["timestamp"]

    # Procesar comando de voz
    nlp_result = procesar_nlp_backend(raw_text)
    tipo = nlp_result["transaction_type"]
    monto = nlp_result["amount"]
    categoria = nlp_result["category"]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Si la voz no contiene nada o falló la grabación
    if raw_text == "Sin transcripción":
        cursor.execute("SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'income'")
        total_ingresos = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'expense'")
        total_gastos = cursor.fetchone()[0] or 0.0
        salud, animo, balance_neto = calcular_estado_mascota(total_ingresos, total_gastos)
        conn.close()
        return jsonify({
            "status": "warning",
            "tipo": "desconocido",
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "balance_neto": balance_neto,
            "salud": salud,
            "animo": animo,
            "alerta_activa": salud < 20 or total_gastos > PRESUPUESTO_DIARIO
        }), 200

    # 1. Si es una consulta de balance
    if tipo == "consulta_balance":
        cursor.execute("SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'income'")
        total_ingresos = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'expense'")
        total_gastos = cursor.fetchone()[0] or 0.0

        salud, animo, balance_neto = calcular_estado_mascota(total_ingresos, total_gastos)

        # Actualizar estado de la mascota en BD
        cursor.execute("UPDATE estado_mascota SET salud = ?, animo = ? WHERE id = 1", (salud, animo))
        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "tipo": "consulta_balance",
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "balance_neto": balance_neto,
            "salud": salud,
            "animo": animo,
            "alerta_activa": salud < 20 or total_gastos > PRESUPUESTO_DIARIO,
        }), 200

    # 2. Si es una nueva transacción (Ingreso o Gasto)
    try:
        cursor.execute(
            """
            INSERT INTO transacciones (message_id, device_id, timestamp, transaction_type, amount, category, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (message_id, device_id, timestamp, tipo, monto, categoria, raw_text),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"status": "error", "message": "message_id duplicado"}), 409

    # Recalcular acumulados del día tras la transacción guardada
    cursor.execute("SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'income'")
    total_ingresos = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(amount) FROM transacciones WHERE transaction_type = 'expense'")
    total_gastos = cursor.fetchone()[0] or 0.0

    # Recalcular salud y ánimo reales
    salud, animo, balance_neto = calcular_estado_mascota(total_ingresos, total_gastos)

    # Si fue un ingreso directo, recuperar un bono de salud extra
    if tipo == "income":
        salud = min(100, salud + 15)
        if salud > 50:
            animo = "FELIZ"

    # Actualizar estado en BD
    cursor.execute("UPDATE estado_mascota SET salud = ?, animo = ? WHERE id = 1", (salud, animo))
    conn.commit()
    conn.close()

    alerta_activa = (total_gastos > PRESUPUESTO_DIARIO) or (salud < 20)

    return jsonify({
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
        "balance_neto": balance_neto,
    }), 201


if __name__ == "__main__":
    init_sqlite()
    print("=========================================================")
    print("🚀 SERVIDOR BACKEND FINAGOTCHI INICIADO")
    print("👉 Límite Presupuesto Diario: $30,000 COP")
    print("👉 Base de Datos: SQLite (finagotchi.db)")
    print("=========================================================\n")
    app.run(debug=True, port=5000)